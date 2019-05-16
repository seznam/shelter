"""
Run production server.
"""

import ctypes
import logging
import multiprocessing
import os
import signal
import sys
import time

import setproctitle
import six

import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.process

from shelter.core.app import get_tornado_apps
from shelter.core.commands import BaseCommand
from shelter.core.constants import TORNADO_WORKER
from shelter.core.exceptions import ProcessError, CommandError
from shelter.utils.imports import import_object

SIGNALS_TO_NAMES_DICT = {
    getattr(signal, n): n for n in dir(signal) if
    n.startswith('SIG') and '_' not in n
}


class ProcessWrapper(object):
    """
    Container for process, provides API for controlling processes.
    *process_cls* is class of the process, either service process
    or Tornado's HTTP server process. *args* are arguments which
    are handled into process constructor. If *wait_unless_ready* is
    :data:`True`, wait maximum *timeout* seconds unless process is
    started, otherwise raise :exc:`shelter.core.exceptions.ProcessError`
    exception if time is exceeded. If *timeout* is :data:`None`,
    wait infinity seconds.
    """

    def __init__(
            self, process_cls, process_args, wait_unless_ready=True,
            timeout=None, name=None):

        self._process = None
        self._process_cls = process_cls
        self._process_args = process_args
        self._wait_unless_ready = wait_unless_ready
        self._timeout = timeout

        self.name = name if name is not None else process_cls.__name__

    if six.PY3:
        def __bool__(self):
            return self.is_alive
    else:
        def __nonzero__(self):
            return self.is_alive

    @property
    def pid(self):
        """
        Either **PID** of the process or :data:`None` if process has
        not been run yet.
        """
        if self._process is None:
            return None
        return self._process.pid

    @property
    def exitcode(self):
        """
        Process exit code. :const:`0` when process exited successfully,
        positive number when exception was occurred, negative number when
        process was signaled and :data:`None` when process has not exited
        yet.
        """
        if self._process is None:
            raise ProcessError(
                "Process '%s' has not been started yet" % self.name)
        return self._process.exitcode

    @property
    def has_started(self):
        """
        :data:`True` when process has been started, else :data:`False`.
        """
        return self._process is not None

    @property
    def is_alive(self):
        """
        :const:`True` when process has been run and has not exited yet,
        else :const:`False`.
        """
        if self._process is None:
            return False
        return self._process.is_alive()

    def start(self):
        """
        Run the process.
        """
        if self:
            raise ProcessError(
                "Process '%s' has been already started" % self.name)
        first_run = not self.has_started
        # Run process
        self._process = self._process_cls(*self._process_args)
        self._process.daemon = False
        self._process.start()
        # Wait unless process is successfully started
        if first_run and self._wait_unless_ready:
            if self._timeout:
                stop_time = time.time() + self._timeout
                while time.time() < stop_time and not self._process.ready:
                    time.sleep(0.25)
                if not self._process.ready:
                    raise ProcessError(
                        "Timeout during start process '%s'" % self.name)
            else:
                while not self._process.ready:
                    time.sleep(0.25)

    def stop(self):
        """
        Stop the process.
        """
        if self:
            self._process.stop()


class TornadoProcess(multiprocessing.Process):
    """
    Tornado HTTP worker.
    """

    def __init__(self, tornado_app, sockets):
        super(TornadoProcess, self).__init__()

        self._http_server = None
        self._parent_pid = os.getpid()
        self._ready = multiprocessing.Value(ctypes.c_bool, False)
        self._sockets = sockets
        self._tornado_app = tornado_app

        self.context = self._tornado_app.settings['context']
        self.http_server = None
        self.logger = logging.getLogger(
            "{:s}.{:s}".format(__name__, self.__class__.__name__))

    @property
    def ready(self):
        """
        :data:`True` when HTTP worker has been started successfully,
        else :data:`False`.
        """
        return self._ready.value

    def stop(self):
        """
        Stop the worker.
        """
        if self._http_server is not None:
            self._http_server.stop()
        tornado.ioloop.IOLoop.instance().add_callback(
            tornado.ioloop.IOLoop.instance().stop)

    def run(self):
        """
        Tornado worker which handles HTTP requests.
        """
        setproctitle.setproctitle("{:s}: worker {:s}".format(
            self.context.config.name,
            self._tornado_app.settings['interface'].name))
        self.logger.info(
            "Worker '%s' has been started with pid %d",
            self._tornado_app.settings['interface'].name, os.getpid())

        # Configure logging
        self.context.config.configure_logging()
        # Create HTTP server instance
        self.http_server = tornado.httpserver.HTTPServer(self._tornado_app)
        # Initialize child
        self.context.initialize_child(TORNADO_WORKER, process=self)

        # Register SIGINT handler which will stop worker
        def sigint_handler(unused_signum, unused_frame):
            """
            Call :meth:`stop` method when SIGINT is reached.
            """
            io_loop = tornado.ioloop.IOLoop.instance()
            io_loop.add_callback_from_signal(self.stop)
        signal.signal(signal.SIGINT, sigint_handler)

        # Register callback which is called when IOLoop is started
        def run_ioloop_callback():
            """
            Set ready flag. Callback is called when worker is started.
            """
            self._ready.value = True
        tornado.ioloop.IOLoop.instance().add_callback(run_ioloop_callback)

        # Register job which will stop worker if parent process PID is changed
        def check_parent_callback():
            """
            Tornado's callback function which checks PID of the parent
            process. If PID of the parent process is changed (parent has
            stopped), call :meth:`stop` method.
            """
            if os.getppid() != self._parent_pid:
                self.stop()
        stop_callback = tornado.ioloop.PeriodicCallback(
            check_parent_callback, 250)
        stop_callback.start()

        # Run HTTP server
        self.http_server.add_sockets(self._sockets)
        # Run IOLoop
        tornado.ioloop.IOLoop.instance().start()


class RunServer(BaseCommand):
    """
    Management command which runs production server.
    """

    name = 'runserver'
    help = 'run server'

    main_pid = None
    processes = []

    def initialize(self):
        """
        Initialize instance attributes. You can override this method in
        the subclasses.
        """
        self.main_pid = os.getpid()
        self.processes.extend(self.init_service_processes())
        self.processes.extend(self.init_tornado_workers())

    def sigusr1_handler(self, unused_signum, unused_frame):
        """
        Handle SIGUSR1 signal. Call function which is defined in the
        **settings.SIGUSR1_HANDLER**. If main process, forward the
        signal to all child processes.
        """
        for process in self.processes:
            if process.pid and os.getpid() == self.main_pid:
                try:
                    os.kill(process.pid, signal.SIGUSR1)
                except ProcessLookupError:
                    pass
        if self._sigusr1_handler_func is not None:
            self._sigusr1_handler_func(self.context)

    def init_service_processes(self):
        """
        Prepare processes defined in the **settings.SERVICE_PROCESSES**.
        Return :class:`list` of the :class:`ProcessWrapper` instances.
        """
        processes = []

        for process_struct in getattr(
                self.context.config.settings, 'SERVICE_PROCESSES', ()):
            process_cls = import_object(process_struct[0])
            wait_unless_ready, timeout = process_struct[1], process_struct[2]

            self.logger.info("Init service process '%s'", process_cls.__name__)

            processes.append(
                ProcessWrapper(
                    process_cls, (self.context,),
                    wait_unless_ready=wait_unless_ready,
                    timeout=timeout
                )
            )

        return processes

    def init_tornado_workers(self):
        """
        Prepare worker instances for all Tornado applications. Return
        :class:`list` of the :class:`ProcessWrapper` instances.
        """
        workers = []

        for tornado_app in get_tornado_apps(self.context, debug=False):
            interface = tornado_app.settings['interface']

            if not interface.port and not interface.unix_socket:
                raise ValueError(
                    'Interface MUST listen either on TCP '
                    'or UNIX socket or both')

            name, processes, host, port, unix_socket = (
                interface.name, interface.processes,
                interface.host, interface.port, interface.unix_socket)
            if processes <= 0:
                processes = tornado.process.cpu_count()
            sockets = []
            listen_on = []

            if port:
                sockets.extend(tornado.netutil.bind_sockets(port, host))
                listen_on.append("{:s}:{:d}".format(host, port))
            if unix_socket:
                sockets.append(tornado.netutil.bind_unix_socket(unix_socket))
                listen_on.append("{:s}".format(interface.unix_socket))

            self.logger.info(
                "Init %d worker(s) for interface '%s' (%s)",
                processes, name, ", ".join(listen_on))

            for dummy_i in six.moves.range(processes):
                worker = ProcessWrapper(
                    TornadoProcess, (tornado_app, sockets),
                    wait_unless_ready=True, timeout=5.0,
                    name=name
                )
                workers.append(worker)

        return workers

    def start_processes(self, max_restarts=-1):
        """
        Start processes and check their status. When some process crashes,
        start it again. *max_restarts* is maximum amount of the restarts
        across all processes. *processes* is a :class:`list` of the
        :class:`ProcessWrapper` instances.
        """
        while 1:
            for process in self.processes:
                if not process:
                    # When process has not been started, start it
                    if not process.has_started:
                        process.start()
                        continue
                    # When process has stopped, start it again
                    exitcode = process.exitcode
                    if exitcode != 0:
                        # Process has been signaled or crashed
                        if exitcode > 0:
                            self.logger.error(
                                "Process '%s' with pid %d died with exitcode "
                                "%d", process.name, process.pid, exitcode
                            )
                        else:
                            self.logger.error(
                                "Process '%s' with pid %d died due to %s",
                                process.name, process.pid,
                                SIGNALS_TO_NAMES_DICT[abs(exitcode)]
                            )
                        # Max restarts has been reached, exit
                        if not max_restarts:
                            msg = "Too many child restarts"
                            self.logger.fatal(msg)
                            raise CommandError(msg)
                        # Start process again
                        process.start()
                        # Decrement max_restarts counter
                        if max_restarts > 0:
                            max_restarts -= 1
                    else:
                        # Process has stopped without error
                        self.logger.info(
                            "Process '%s' with pid %d has stopped",
                            process.name, process.pid
                        )
                        # Start process again
                        process.start()
                        self.logger.info(
                            "Process '%s' has been started with pid %d",
                            process.name, process.pid
                        )
            else:
                time.sleep(0.25)
                continue
            break

    def command(self):
        """
        **runserver** command implementation.
        """
        setproctitle.setproctitle(
            "{:s}: master process '{:s}'".format(
                self.context.config.name, " ".join(sys.argv)
            ))

        try:
            # Init and start processes
            self.start_processes(max_restarts=100)
        except KeyboardInterrupt:
            pass
        finally:
            # Stop processes
            for process in self.processes:
                self.logger.info(
                    "Stopping proces '%s' with pid %d",
                    process.name, process.pid)
                process.stop()
