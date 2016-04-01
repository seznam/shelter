"""
Module :module:`shelter.core.config` provides base class which
encapsulates configuration.
"""

import collections
import glob
import logging
import os.path
import sys

import six.moves

from shelter.core.context import Context
from shelter.utils.imports import import_object
from shelter.utils.net import parse_host

__all__ = ['Config']

logger = logging.getLogger(__name__)

CONFIGPARSER_EXC = (
    six.moves.configparser.NoSectionError,
    six.moves.configparser.NoOptionError,
)


def get_conf_d_files(path):
    """
    Return alphabetical ordered :class:`list` of the *.conf* files
    placed in the path. *path* is a directory path.

    ::

        >>> get_conf_d_files('conf/conf.d/')
        ['conf/conf.d/10-base.conf', 'conf/conf.d/99-dev.conf']
    """
    if not os.path.isdir(path):
        raise ValueError("'%s' is not a directory" % path)
    files_mask = os.path.join(path, "*.conf")
    return [f for f in sorted(glob.glob(files_mask)) if os.path.isfile(f)]


def get_conf_files(filename):
    """
    Return :class:`list` of the all configuration files. *filename* is a
    path of the main configuration file.

    ::

        >>> get_conf_files('exampleapp.conf')
        ['exampleapp.conf', 'exampleapp.conf.d/10-database.conf']
    """
    if not os.path.isfile(filename):
        raise ValueError("'%s' is not a file" % filename)
    conf_d_path = "%s.d" % filename
    if not os.path.exists(conf_d_path):
        return [filename]
    else:
        return [filename] + get_conf_d_files(conf_d_path)


def get_configparser(filename=''):
    """
    Read main configuration file and all files from *conf.d* subdirectory
    and return parsed configuration as a **configparser.RawConfigParser**
    instance.
    """
    parser = six.moves.configparser.RawConfigParser()
    filename = filename or os.environ.get('SHELTER_CONFIG_FILENAME', '')
    if filename:
        for conf_file in get_conf_files(filename):
            logger.info("Found config '%s'", conf_file)
            if not parser.read(conf_file):
                logger.warning("Error while parsing config '%s'", conf_file)
    return parser


class Config(object):
    """
    Class which encapsulates all configurations. It joins options from
    settings module, configuration file and command line arguments.
    *settings* is a Python's module defined by **SHELTER_SETTINGS_MODULE**
    environment variable or **-s/--settings** command line argument,
    *config_parser* is a :class:`configparser.RawConfigParser` instance
    (Py2)/:class:`ConfigParser.RawConfigParser` (Py3) and *args_parser*
    is a :class:`argparse.Namespace` instance.
    """

    Interface = collections.namedtuple(
        'Interface', ['name', 'host', 'port', 'processes', 'urls']
    )
    """
    Container which encapsulates arguments of the interface.
    """

    def __init__(self, settings, config_parser, args_parser):
        self._settings = settings
        self._config_parser = config_parser
        self._args_parser = args_parser
        self._cached_values = {}

    def __repr__(self):
        return "<{}.{}: {:#x}>".format(
            self.__class__.__module__, self.__class__.__name__, id(self)
        )

    @property
    def settings(self):
        """
        Settings module of the application.
        """
        return self._settings

    @property
    def config_parser(self):
        """
        Parsed configuration file as a **configparser.RawConfigParser**
        instance.
        """
        return self._config_parser

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
                interface_name = 'interface_%s' % name
                # Hostname + port
                try:
                    host, port = parse_host(
                        self.config_parser.get(interface_name, 'Listen'))
                except CONFIGPARSER_EXC:
                    host, port = parse_host(interface['LISTEN'])
                # Processes
                try:
                    processes = self.config_parser.getint(
                        interface_name, 'Processes')
                except CONFIGPARSER_EXC:
                    processes = int(interface.get('PROCESSES', 1))
                # Urls
                try:
                    urls_obj_name = self.config_parser.get(
                        interface_name, 'Urls')
                except CONFIGPARSER_EXC:
                    urls_obj_name = interface.get('URLS', '')
                if urls_obj_name:
                    urls = import_object(urls_obj_name)
                else:
                    urls = ()

                self._cached_values['interfaces'].append(
                    self.Interface(name, host, port, processes, urls)
                )
        return self._cached_values['interfaces']

    @property
    def logging(self):
        """
        *Python's logging* configuration or :const:`None`.
        """
        return getattr(self.settings, 'LOGGING', None)

    @property
    def logging_from_config_file(self):
        """
        Read *Python's logging* configuration from configuration file flag.
        """
        return getattr(self.settings, 'LOGGING_FROM_CONFIG_FILE', False)

    @property
    def name(self):
        """
        Application name. It's used as a process name.
        """
        return getattr(self.settings, 'NAME', sys.argv[0])

    @property
    def init_handler(self):
        """
        Either function (handler) which will be run during initialization
        of the applicationon or :const:`None` when no init handler.
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
