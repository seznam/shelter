"""
Shelter provides base functionality for configuration. Configuration
options can be read either from configuration file or from command line
arguments.

Class :class:`shelter.Config` is an container which holds configuration.
Constructor takes two arguments, *settings* and *args_parser*.




Public attributes are **settings** which
is ``settings`` module of the application and **args_parser** which is
instance of the ``argparse.ArgumentParser`` from *Python's standard library*.

You can override this class in the `settings` module::

    CONFIG_CLASS = 'myapp.core.config.AppConfig'

Your own `AppConfig` class can contain additional *properties* with
application's settings, e.g. database connection arguments. Way how the value
is found is only on you - either only in **settings** or **args_parser** or
in both. You can define additional arguments of the command line.

::

    import time

    from shelter.core.config import Config, argument

    class AppConfig(Config):

        arguments = (
            argument(
                '-k', '--secret-key',
                dest='secret_key', action='store',
                type=str, default='',
                help='configuration file'
            ),
        )

        Database = collections.namedtuple('Database', ['host', 'db'])

        def initialize(self):
            # initialize() is called after instance is created. If you want
            # add some instance attributes, use this method instead of
            # override __init__().
            self._server_started_time = time.time()

        def get_config_items(self):
            # Override get_config_items() method if you want to add
            # your options into showconfig management command.
            base_items = super(AppConfig, self).get_config_items()
            app_items = (
                ('secret_key', self.secret_key),
                ('database', self.database),
            )
            return base_items + app_items

        @property
        def secret_key(self):
            # If command-line argument -k/--secret-key exists, it will
            # override settings.SECRET_KEY value.
            return self.args_parser.secret_key or self.settings.SECRET_KEY

        @property
        def database(self):
            return self.Database(
                db=self.settings.DATABASE_NAME,
                host=self.settings.DATABASE_HOST,
                passwd=getattr(self.settings, DATABASE_PASSWORD, '')
            )
"""

import collections
import logging.config
import sys

import six
import tornado.web

from shelter.core.cmdlineparser import argument
from shelter.core.context import Context
from shelter.utils.imports import import_object
from shelter.utils.net import parse_host

__all__ = ['Config', 'argument']

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
    Class which encapsulates configuration. It joins options from
    settings module and command line arguments. *settings* is a Python's
    module defined by either **SHELTER_SETTINGS_MODULE** environment
    variable or **-s/--settings** command line argument and *args_parser*
    is a :class:`argparse.Namespace` instance.
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
    Command line arguments of the Config class.
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
        Initialize instance attributes. You can override this method in
        the subclasses.
        """
        pass

    def configure_logging(self):
        """
        Configure Python's logging according to configuration *config*.
        """
        logging.config.dictConfig(self.logging or BASE_LOGGING)

    def get_config_items(self):
        """
        Return current configuration as a :class:`tuple` with
        option-value pairs.

        ::
            (('option1', value1), ('option2', value2))
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
    def settings(self):
        """
        Settings module of the application.
        """
        return self._settings

    @property
    def args_parser(self):
        """
        Command line arguments as a **argparse**.
        """
        return self._args_parser

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
