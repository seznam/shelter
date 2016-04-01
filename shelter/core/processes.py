"""
Module :module:`shelter.core.processes` provides an ancestor and
functionality for writing service processes.
"""

import copy
import ctypes
import functools
import logging
import multiprocessing
import os
import signal
import threading
import time

import setproctitle
import six

from shelter.core.exceptions import ProcessError
from shelter.utils.logging import AddLoggerMeta, configure_logging

__all__ = ['BaseProcess']


SIGNALS_TO_NAMES_DICT = {
    getattr(signal, n): n for n in dir(signal) if
    n.startswith('SIG') and '_' not in n
}

logger = logging.getLogger(__name__)


class Worker(object):
    """
    Container for worker process - either service process or Tornado's
    HTTP server process. *name* is a name of the worker, *factory* is a
    function which returns instance of the :class:`multiprocessing.Process`
    and *args* are arguments which are handled into *factory* function.
    """

    def __init__(self, name, factory, args):
        self.name = name
        self.factory = factory
        self.args = args
        self.process = None

    if six.PY3:
        def __bool__(self):
            return self.is_alive
    else:
        def __nonzero__(self):
            return self.is_alive

    def start(self, wait_unless_ready=True, timeout=None):
        """
        Run the *worker*. If *wait_unless_ready* is :const:`True`,
        wait maximum *timeout* seconds unless worker is started or
        raise :exc:`shelter.core.exceptions.ProcessError` exception
        if time is exceeded. If *timeout* is :const:`None`, wait
        infinity seconds.
        """
        # Run process
        if self:
            raise ProcessError("Worker '%s' is runnig" % self.name)
        else:
            self.process = self.factory(self.args)
            self.process.daemon = False
            self.process.start()
        # Wait unless worker is started
        if wait_unless_ready:
            if timeout:
                stop_time = time.time() + timeout
                while time.time() < stop_time and not self.process.ready:
                    time.sleep(0.1)
                if not self.process.ready:
                    raise ProcessError(
                        "Timeout during start service process '%s'" %
                        self.name)
            else:
                while not self.process.ready:
                    time.sleep(0.1)

    @property
    def pid(self):
        """
        Either **PID** of the worker process or :const:`None` if worker
        has not run yet.
        """
        if self.process is not None:
            return self.process.pid
        else:
            return None

    @property
    def exitcode(self):
        """
        Worker's exit code. :const:`0` when worker exited successfully,
        positive number when exception was occurred, negative number when
        worker was signaled and :const:`None` when worker has not exited
        yet.
        """
        return self.process.exitcode

    @property
    def has_started(self):
        """
        :const:`True` when worker has been started, else :const:`False`.
        """
        return self.process is not None

    @property
    def is_alive(self):
        """
        :const:`True` when has not exited yet, else :const:`False`.
        """
        if self.process is not None:
            return self.process.is_alive()
        else:
            return False


def start_workers(workers, max_restarts=-1):
    """
    Start *workers* and check their status. When some worker crashes,
    start it again. *max_restarts* is maximum amount of the restarts
    across all workers. *workers* is a :class:`list` of the :class:`Worker`
    instances.
    """
    while 1:
        for worker in workers:
            if not worker:
                # When worker has not been started, start it
                if not worker.has_started:
                    worker.start()
                    continue
                # When worker has been signaled or crashed, start it again
                # and decrement max_restarts counter
                exitcode = worker.exitcode
                if exitcode != 0:
                    if exitcode > 0:
                        logger.error(
                            "Worker '%s' with pid %d died due to error",
                            worker.name, worker.pid
                        )
                    else:
                        logger.error(
                            "Worker '%s' with pid %d died due to %s",
                            worker.name, worker.pid,
                            SIGNALS_TO_NAMES_DICT[abs(exitcode)]
                        )
                    # Max restarts has been reached, exit
                    if not max_restarts:
                        logger.fatal("Too many child restarts")
                        break
                    # Start worker again and decrement max_restarts counter
                    worker.start()
                    if max_restarts > 0:
                        max_restarts -= 1
                    continue
        else:
            time.sleep(0.1)
            continue
        break


class BaseProcess(six.with_metaclass(AddLoggerMeta, object)):
    """
    Ancestor for service processes. Adjust :attribute:`interval` attribute
    and override method :meth:`loop` which is repeatedly called every
    :attribute:`interval` seconds.

    .. note::

        Do not create new instance using contructor, it is necessary to
        create new instance using :meth:`get_instance` static method!
    """

    lock_cls = type(
        'DummyLock', (object,), {
            'acquire': lambda *args: False,
            'release': lambda: None
        }
    )
    ready_cls = bool
    separate_process = None

    interval = 0
    """
    Interval in seconds. After this time :meth:`loop` method is
    repeatedly called.
    """

    def __init__(self, context):
        if self.separate_process is None:
            raise ProcessError(
                "New instance must be created using get_instance class-method")
        super(BaseProcess, self).__init__()

        self._parent_pid = os.getpid()
        self._lock = self.lock_cls()
        self._ready = self.ready_cls(False)

        if self.separate_process:
            self.context = context
            self.daemon = False
        else:
            self.context = copy.copy(context)
            self.daemon = True
        self.name = "{:s}: {:s}".format(
            self.context.config.name, self.__class__.__name__)

    @classmethod
    def get_instance(cls, context, separate_process=True):
        """
        Create and return instance of the service process. According to
        *separate_process* argument service process will be run either in
        separated process or in thread.
        """
        if separate_process:
            ancestor_cls = multiprocessing.Process
            lock_cls = functools.partial(multiprocessing.Lock)
            ready_cls = functools.partial(multiprocessing.Value, ctypes.c_bool)
        else:
            ancestor_cls = threading.Thread
            lock_cls = functools.partial(threading.Lock)
            ready_cls = functools.partial(ctypes.c_bool)

        process_cls = type(
            cls.__name__, (cls, ancestor_cls), {
                '__module__': cls.__module__,
                'lock_cls': lock_cls,
                'ready_cls': ready_cls,
                'separate_process': separate_process,
            }
        )
        return process_cls(context)

    def run(self):
        """
        Repeatedly call :meth:`loop` method every :attribute:`interval`
        seconds. In case of *separate_process* is :const:`True` exit
        when parent process has exited.
        """
        if self.separate_process:
            setproctitle.setproctitle(self.name)

            configure_logging(self.context.config)

            # Register SIGINT handler which will exit service process
            def sigint_handler(dummy_signum, dummy_frame):
                """
                Exit service process when SIGINT is reached.
                """
                self._parent_pid = 0
            signal.signal(signal.SIGINT, sigint_handler)

        next_loop_time = 0
        while 1:
            # Exit if service process is run in separated process and pid
            # of the parent process has changed (parent process has exited
            # and init is new parent).
            if self.separate_process and os.getppid() != self._parent_pid:
                break
            # Repeatedly call loop method. After first call set ready flag.
            if time.time() >= next_loop_time:
                self.loop()
                if not next_loop_time and not self.ready:
                    self._lock.acquire()
                    try:
                        self._ready.value = True
                    finally:
                        self._lock.release()
                next_loop_time = time.time() + self.interval
            else:
                time.sleep(0.1)

    def loop(self):
        """
        Repeatedly in interval :attribute:`interval` do code in this
        method. It is abstract method, override it in subclasses.
        """
        raise NotImplementedError

    @property
    def ready(self):
        """
        :const:`True` when service process has been started successfully,
        else :const:`False`.
        """
        self._lock.acquire()
        try:
            return self._ready.value
        finally:
            self._lock.release()
