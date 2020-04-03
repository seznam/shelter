"""
Shelter provides base functionality for configuration. Configuration
options can be read either from :mod:`settings` or from command line
arguments. During start Shelter creates instance of the :class:`Config`
class. It is container which holds configuration. Constructor takes two
arguments, *settings* and *args_parser*. You can override and customize
this class in your application. It is possible to add additional command
line arguments or options from :mod:`settings` module.

Consider customized ``Config`` class:

.. code-block:: python

    import collections
    import os

    from shelter.core import config

    DatabaseConfig = collections.namedtuple(
        'Database', ['db', 'host', 'port', 'user', 'password'])

    STR2BOOL = {'0': False, 'false': False, '1': True, 'true': True}


    class Config(config.Config):

        arguments = (
            config.argument(
                '-d', '--log-debug', action='store_true',
                help='log debug messages'),
        )

        def initialize(self):
            # Obtain value for log_debug flag. If MYAPP_LOG_DEBUG environment
            # variable is set, obtain value from environment variable. If not
            # and --log-debug command line argument is passed, set log_debug
            # to True, otherwise set log_debug to False.
            log_debug = os.environ.get('MYAPP_LOG_DEBUG')
            if log_debug is not None:
                if log_debug not in STR2BOOL:
                    raise ValueError(
                        "Invalid log_debug value '{}'".format(log_debug))
                self._log_debug = STR2BOOL[log_debug.lower()]
            else:
                self._log_debug = self.args_parser.log_debug

        def get_config_items(self):
            # Override get_config_items() method if you want to add your
            # options into showconfig management command.
            app_options = (
                ('log_debug', self.log_debug),
                ('database', self.database),
            )
            return super(Config, self).get_config_items() + app_options

        @property
        def log_debug(self):
            return self._log_debug

        @property
        def database(self):
            return DatabaseConfig(
                db=self.settings.DATABASE['db'],
                host=self.settings.DATABASE['host'],
                port=self.settings.DATABASE['port'],
                user=self.settings.DATABASE['user'],
                password=self.settings.DATABASE.get('password'),
            )

Class adds additional command line argument :option:`-d/--log-debug`,
whose value can be set in command line, or via :envvar:`MYAPP_LOG_DEBUG`
environment variable. If both are present, environment variable has
higher priority. Final value is accesible as :attr:`config.log_debug`
property. Class also adds database configuration as :attr:`config.database`
property. For better performance, consider using :obj:`cached_property`
instead of :obj:`!property`.
"""

import collections
import logging.config
import sys

import six
import tornado.web

from shelter.core import cmdlineparser
from shelter.core.context import Context
from shelter.utils.imports import import_object
from shelter.utils.net import parse_host

__all__ = ['Config', 'argument']

argument = cmdlineparser.argument

BASE_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'NOTSET',
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


class Config(object):
    """
    Class which encapsulates configuration. The class joins options from
    :mod:`settings` module and command line arguments. *settings* is a
    Python module defined by either :envvar:`SHELTER_SETTINGS_MODULE`
    environment variable or :option:`-s/--settings` command line argument.
    *args_parser* is instance of :class:`argparse.Namespace`.
    """

    Interface = collections.namedtuple(
        'Interface', [
            'name', 'host', 'port', 'unix_socket',
            'processes', 'urls', 'app_cls']
    )
    """
    Container which encapsulates arguments of the interface.
    """

    arguments = ()
    """
    User defined command line arguments. Arguments are defined by
    :func:`argument` function. For argument's details see :mod:`argparse`
    module documentation.

    .. code-block:: python

        arguments = (
            argument('-d', action='store_true', help='log debug messages'),
        )
    """

    def __init__(self, settings, args_parser):
        self._settings = settings
        self._args_parser = args_parser
        self._cached_values = {}
        self.initialize()

    def __repr__(self):
        return "<{}.{}: {:#x}>".format(
            self.__class__.__module__, self.__class__.__name__, id(self)
        )

    def initialize(self):
        """
        Initialize instance attributes. You can override this method
        in the subclasses. If you want to add some instance attributes,
        do not override :meth:`__init__` constructor, but define these
        attributes inside this method.

        .. code-block:: python

            def initialize(self):
                self.some_attribute = self.context.some_value
        """
        pass

    @property
    def settings(self):
        """
        :mod:`settings` module of the application.
        """
        return self._settings

    @property
    def args_parser(self):
        """
        Command line arguments as instance of :class:`argparse.Namespace`.
        """
        return self._args_parser

    def configure_logging(self):
        """
        Configure Python's logging according to configuration *config*.
        """
        logging.config.dictConfig(self.logging or BASE_LOGGING)

    def get_config_items(self):
        """
        Return current configuration as a :class:`!tuple` with
        option-value pairs. Management command :option:`showconfig`
        shows effective configuration of your application. If you
        override :class:`Config` class and you want to show your own
        configuration options, it is necessary to register these
        options.

        .. code-block:: python

            def get_config_items(self):
                app_options = (
                    ('database', self.database),
                )
                return super(Config, self).get_config_items() + app_options
        """
        return (
            ('settings', self.settings),
            ('context_class', self.context_class),
            ('interfaces', self.interfaces),
            ('logging', self.logging),
            ('name', self.name),
            ('init_handler', self.init_handler),
            ('sigusr1_handler', self.sigusr1_handler),
            ('sigusr2_handler', self.sigusr2_handler),
        )

    @property
    def context_class(self):
        """
        Context as a :class:`shelter.core.context.Context` class or subclass.
        """
        if 'context_class' not in self._cached_values:
            context_cls_name = getattr(self.settings, 'CONTEXT_CLASS', '')
            if context_cls_name:
                context_class = import_object(context_cls_name)
            else:
                context_class = Context
            self._cached_values['context_class'] = context_class
        return self._cached_values['context_class']

    @property
    def interfaces(self):
        """
        Interfaces as a :class:`list`of the
        :class:`shelter.core.config.Config.Interface` instances.
        """
        if 'interfaces' not in self._cached_values:
            self._cached_values['interfaces'] = []
            for name, interface in six.iteritems(self.settings.INTERFACES):
                listen = interface.get('LISTEN')
                unix_socket = interface.get('UNIX_SOCKET')
                if not listen and not unix_socket:
                    raise ValueError(
                        'Interface MUST listen either on TCP '
                        'or UNIX socket or both')
                host, port = parse_host(listen) if listen else (None, None)
                processes = int(interface.get('PROCESSES', 1))
                urls_obj_name = interface.get('URLS', '')
                if urls_obj_name:
                    urls = import_object(urls_obj_name)
                else:
                    urls = ()
                app_cls_name = interface.get('APP_CLASS', '')
                if app_cls_name:
                    app_cls = import_object(app_cls_name)
                else:
                    app_cls = tornado.web.Application
                interface = self.Interface(
                    name, host, port, unix_socket, processes, urls, app_cls)
                self._cached_values['interfaces'].append(interface)
        return self._cached_values['interfaces']

    @property
    def logging(self):
        """
        *Python's logging* configuration or :const:`None`.
        """
        return getattr(self.settings, 'LOGGING', None)

    @property
    def command_name(self):
        """
        Name of the current management command.
        """
        return self._args_parser.action

    @property
    def name(self):
        """
        Application name. It's used as a process name.
        """
        return getattr(self.settings, 'NAME', sys.argv[0])

    @property
    def init_handler(self):
        """
        Either name of the function or :class:`list` containing functions
        names which will be run during initialization of the applicationon.
        :const:`None` when no init handler.
        """
        return getattr(self.settings, 'INIT_HANDLER', None)

    @property
    def sigusr1_handler(self):
        """
        Either function (handler) which will be run on SIGUSR1 or
        :const:`None` when no signal handler.
        """
        return getattr(self.settings, 'SIGUSR1_HANDLER', None)

    @property
    def sigusr2_handler(self):
        """
        Either function (handler) which will be run on SIGUSR2 or
        :const:`None` when no signal handler.
        """
        return getattr(self.settings, 'SIGUSR2_HANDLER', None)

    @property
    def app_settings_handler(self):
        """
        Either function which will be called when instance of the Tornado
        application is created or :const:`None` when no handler.. Return
        :class:`dict` which is passed as `**settings` argument into
        ``tornado.web.Application`` constructor.
        """
        return getattr(self.settings, 'APP_SETTINGS_HANDLER', None)
