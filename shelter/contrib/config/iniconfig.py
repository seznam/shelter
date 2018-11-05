"""
Module :module:`shelter.contrib.config.iniconfig` provides **INI files**
configuration.
"""

import glob
import logging.config
import os.path

from gettext import gettext as _

import six.moves

from shelter.core.exceptions import ImproperlyConfiguredError
from shelter.core.config import Config, argument
from shelter.utils.imports import import_object
from shelter.utils.net import parse_host

__all__ = ['IniConfig']

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
    return [filename] + get_conf_d_files(conf_d_path)


def get_configparser(filename=''):
    """
    Read main configuration file and all files from *conf.d* subdirectory
    and return parsed configuration as a **configparser.RawConfigParser**
    instance.
    """
    filename = filename or os.environ.get('SHELTER_CONFIG_FILENAME', '')
    if not filename:
        raise ImproperlyConfiguredError(_(
            "Configuration file is not defined. You must either "
            "set 'SHELTER_CONFIG_FILENAME' environment variable or "
            "'-f/--config-file' command line argument."
        ))

    parser = six.moves.configparser.RawConfigParser()
    for conf_file in get_conf_files(filename):
        logger.info("Found config '%s'", conf_file)
        if not parser.read(conf_file):
            logger.warning("Error while parsing config '%s'", conf_file)
    return parser


class IniConfig(Config):
    """
    Class which extends base :class:`shelter.core.config.Config`. Provides
    configuration from **INI** files. Configuration file is specified
    either by 'SHELTER_CONFIG_FILENAME' environment variable or
    '-f/--config-file' command line argument.

    First, main configuration file is read. Then all configuration files
    from `file.conf.d` subdirectory are read in alphabetical order. E.g.
    if `-f conf/myapp.conf` is handled, first `conf/myapp.conf` file is
    read and then all `conf/myapp.conf.d/*.conf` files. Value in later
    configuration file overrides previous defined value.
    """

    arguments = (
        argument(
            '-f', '--config-file',
            dest='config', action='store', type=str, default=None,
            help=_('configuration file')
        ),
    )

    def __init__(self, settings, args_parser):
        self._config_parser = get_configparser(args_parser.config)
        super(IniConfig, self).__init__(settings, args_parser)

    def configure_logging(self):
        """
        Configure Python's logging according to configuration placed in
        configuration file.
        """
        logging.config.fileConfig(
            self.config_parser, disable_existing_loggers=False)

    @property
    def config_parser(self):
        """
        Parsed configuration file as a **configparser.RawConfigParser**
        instance.
        """
        return self._config_parser

    @property
    def name(self):
        """
        Application name. It's used as a process name.
        """
        try:
            return self.config_parser.get('application', 'name')
        except CONFIGPARSER_EXC:
            return super(IniConfig, self).name

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
                # Hostname:port + unix socket
                try:
                    listen = self.config_parser.get(interface_name, 'Listen')
                except CONFIGPARSER_EXC:
                    listen = interface.get('LISTEN')
                try:
                    unix_socket = self.config_parser.get(
                        interface_name, 'UnixSocket')
                except CONFIGPARSER_EXC:
                    unix_socket = interface.get('UNIX_SOCKET')
                if not listen and not unix_socket:
                    raise ValueError(
                        'Interface MUST listen either on TCP '
                        'or UNIX socket or both')
                host, port = parse_host(listen) if listen else (None, None)
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
                    self.Interface(
                        name, host, port, unix_socket, processes, urls)
                )
        return self._cached_values['interfaces']
