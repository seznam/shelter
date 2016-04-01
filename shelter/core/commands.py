"""
Module :module:`shelter.core.Commands` provides an ancestor and
functionality for writing management commands.
"""

import signal
import os
import sys

import six

from shelter.core.processes import Worker
from shelter.utils.imports import import_object
from shelter.utils.logging import AddLoggerMeta, configure_logging

__all__ = ['BaseCommand', 'argument']


def argument(*args, **kwargs):
    """
    Return function's arguments how single command line argument should
    be parsed. *args* a *kwargs* have the same meaning as a
    :method:`argparse.ArgumentParser.add_argument` method.
    """
    return args, kwargs


class BaseCommand(six.with_metaclass(AddLoggerMeta, object)):
    """
    Ancestor for management commands. Inherit this class and adjust
    *name* and *help* and optionally *arguments* attributes and override
    *command()* method. *arguments* is :class:`tuple` containing command
    line arguments for management command. Classes (each class represents
    one management command) are registered in the
    **settings.MANAGEMENT_COMMANDS** option. Constructor's argument
    *config* is instance of the :class:`shelter.core.config.Config`.

    ::

        # application/commands/hello.py

        class HelloCommand(BaseCommand):

            name = 'hello'
            help = 'show hello'
            arguments = (
                argument('--name', dest='name', help='your name'),
            )

            def command(self):
                print("Hello %s" % self.args.name)


        # application/settings.py

        MANAGEMENT_COMMANDS = (
            'application.commands.hello.HelloWorld',
        )
    """

    logger = None

    help = ''
    """
    Description of the management command.
    """

    arguments = ()
    """
    Command line arguments of the management command.
    """

    service_processes_start = False
    """
    Start service processes flag. If :const:`True`, management command
    will start service processes.
    """

    service_processes_in_thread = True
    """
    Start service processes in the thread flag. If :const:`True`,
    service processes will be started in the threads, if :const:`False`,
    service processes will be started in the separate processes.
    """

    settings_required = True
    """
    Settings module required flag. If :const:`True`, settings module
    is necessary for start the application.
    """

    def __init__(self, config):
        self.context = config.context_class.from_config(config)
        self.stdout = sys.stdout
        self.stderr = sys.stderr
        self.pid = os.getpid()
        self.workers = []
        self.initialize()

    def __call__(self):
        config = self.context.config

        # Initialize logging
        configure_logging(config)

        # Call application init handler
        if config.init_handler:
            init_handler = import_object(config.init_handler)
            init_handler(self.context)
        # Register SIGUSR1 handler
        if config.sigusr1_handler:
            sigusr1_handler = import_object(config.sigusr1_handler)

            def sigusr1_signal_handler(dummy_signum, dummy_frame):
                """
                Handle SIGUSR2 signal. Call function which is defined
                in the **settings.SIGUSR2_HANDLER** setting and forward
                signal to all workers.
                """
                sigusr1_handler(self.context)
                if (self.pid == os.getpid() and
                        not self.service_processes_in_thread):
                    for worker in self.workers:
                        if worker.process:
                            os.kill(worker.process.pid, signal.SIGUSR1)
            signal.signal(signal.SIGUSR1, sigusr1_signal_handler)
        else:
            signal.signal(signal.SIGUSR1, signal.SIG_IGN)
        # Register SIGUSR2 handler
        if config.sigusr2_handler:
            sigusr2_handler = import_object(config.sigusr2_handler)

            def sigusr2_signal_handler(dummy_signum, dummy_frame):
                """
                Handle SIGUSR2 signal. Call function which is defined in
                the **settings.SIGUSR2_HANDLER** setting.
                """
                sigusr2_handler(self.context)
            signal.signal(signal.SIGUSR2, sigusr2_signal_handler)
        else:
            signal.signal(signal.SIGUSR2, signal.SIG_IGN)

        # Start service processes
        if self.service_processes_start:
            self.start_service_processes()
        # Run command
        self.command()
        # Stop service processes
        if not self.service_processes_in_thread:
            for worker in self.workers:
                worker.process.terminate()

    def initialize(self):
        """
        Initialize instance attributes. You can override this method in
        the subclasses.
        """
        pass

    def start_service_processes(self):
        """
        Run service processes defined in the **settings.SERVICE_PROCESSES**.
        According to :attribute:`service_processes_in_thread` attribute run
        service process either in thread, or as a new process.
        """
        settings = self.context.config.settings
        service_processes = getattr(settings, 'SERVICE_PROCESSES', ())
        separate_process = not self.service_processes_in_thread

        for process in service_processes:
            process_cls = import_object(process[0])
            process_name = process_cls.__name__
            wait_unless_ready, timeout = process[1], process[2]

            def worker_factory(args):
                """
                Return instance of the worker.
                """
                process_cls, context, separate_process = args
                return process_cls.get_instance(
                    context, separate_process=separate_process
                )

            self.logger.info("Init management command '%s'", process_name)

            worker = Worker(
                name=process_name,
                factory=worker_factory,
                args=(process_cls, self.context, separate_process)
            )
            worker.start(wait_unless_ready=wait_unless_ready, timeout=timeout)

            self.workers.append(worker)

    def command(self):
        """
        Management command, override this method.
        """
        raise NotImplementedError
