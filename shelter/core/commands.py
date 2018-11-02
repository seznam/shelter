"""
Module :module:`shelter.core.commands` provides an ancestor and
functionality for writing management commands.
"""

import logging
import signal
import sys

from shelter.core.cmdlineparser import argument
from shelter.utils.imports import import_object

__all__ = ['BaseCommand', 'argument']


class BaseCommand(object):
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

        from shelter.core.commands import BaseCommand, argument

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

    help = ''
    """
    Description of the management command.
    """

    arguments = ()
    """
    Command line arguments of the management command.
    """

    settings_required = True
    """
    Settings module required flag. If :const:`True`, settings module
    is necessary for start the application.
    """

    def __init__(self, config):
        self.context = config.context_class.from_config(config)
        self.logger = logging.getLogger(
            "{:s}.{:s}".format(__name__, self.__class__.__name__))
        self.stdout = sys.stdout
        self.stderr = sys.stderr

        self.initialize()

    def initialize(self):
        """
        Initialize instance attributes. You can override this method in
        the subclasses.
        """
        pass

    def __call__(self):
        # Initialize logging
        self._configure_logging()
        # Call application init handler(s)
        self._call_init_handlers()
        # Register signals handlers
        self._register_sigusr1()
        self._register_sigusr2()
        # Run command
        self.command()

    def _configure_logging(self):
        """
        Configure logging.
        """
        self.context.config.configure_logging()

    def _call_init_handlers(self):
        """
        Call init handler(s) defined in the **settings.SIGUSR1_HANDLER**
        settings. Can be either function name or class :class:`list` of
        the function names.
        """
        init_handler_setting = self.context.config.init_handler

        if init_handler_setting:
            if isinstance(init_handler_setting, str):
                init_handlers = [init_handler_setting]
            else:
                init_handlers = init_handler_setting

            for init_handler in init_handlers:
                self.logger.info("Run init handler '%s'" % init_handler)
                init_handler_obj = import_object(init_handler)
                init_handler_obj(self.context)

    def _register_sigusr1(self):
        """
        Register SIGUSR1 signal handler.
        """
        handler_name = self.context.config.sigusr1_handler

        if handler_name:
            self.logger.info("Register SIGUSR1 handler '%s'" % handler_name)
            handler_func = import_object(handler_name)

            def signal_handler(dummy_signum, dummy_frame):
                """
                Handle SIGUSR1 signal. Call function which is defined
                in the **settings.SIGUSR1_HANDLER**.
                """
                handler_func(self.context)
            signal.signal(signal.SIGUSR1, signal_handler)
        else:
            signal.signal(signal.SIGUSR1, signal.SIG_IGN)

    def _register_sigusr2(self):
        """
        Register SIGUSR2 signal handler.
        """
        handler_name = self.context.config.sigusr2_handler

        if handler_name:
            self.logger.info("Register SIGUSR2 handler '%s'" % handler_name)
            handler_func = import_object(handler_name)

            def signal_handler(dummy_signum, dummy_frame):
                """
                Handle SIGUSR2 signal. Call function which is defined in
                the **settings.SIGUSR2_HANDLER** setting.
                """
                handler_func(self.context)
            signal.signal(signal.SIGUSR2, signal_handler)
        else:
            signal.signal(signal.SIGUSR2, signal.SIG_IGN)

    def command(self):
        """
        Management command, override this method.
        """
        raise NotImplementedError
