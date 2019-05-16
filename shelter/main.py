"""
Modul :module:`shelter.main` is an entry point from command line into
**Shelter** application.
"""

import importlib
import itertools
import multiprocessing
import os
import sys
import traceback

from gettext import gettext as _

import six

from shelter.commands import SHELTER_MANAGEMENT_COMMANDS
from shelter.core.exceptions import ImproperlyConfiguredError
from shelter.core.commands import BaseCommand
from shelter.core.cmdlineparser import ArgumentParser
from shelter.core.config import Config
from shelter.utils.imports import import_object


__all__ = ['main']


def get_app_settings(parser, known_args):
    """
    Return **settings** module of the application according to
    either command line argument or **SHELTER_SETTINGS_MODULE**
    environment variable.
    """
    args, dummy_remaining = parser.parse_known_args(known_args)
    settings_module_path = (
        args.settings or os.environ.get('SHELTER_SETTINGS_MODULE', ''))
    if not settings_module_path:
        return None
    return importlib.import_module(settings_module_path)


def get_management_commands(settings):
    """
    Find registered managemend commands and return their classes
    as a :class:`dict`. Keys are names of the management command
    and values are classes of the management command.
    """
    app_commands = getattr(settings, 'MANAGEMENT_COMMANDS', ())
    commands = {}
    for name in itertools.chain(SHELTER_MANAGEMENT_COMMANDS, app_commands):
        command_obj = import_object(name)
        if not issubclass(command_obj, BaseCommand):
            raise ValueError("'%s' is not subclass of the BaseCommand" % name)
        commands[command_obj.name] = command_obj
    return commands


def get_config_class(settings):
    """
    According to **settings.CONFIG_CLASS** return either config class
    defined by user or default :class:`shelter.core.config.Config`.
    """
    config_cls_name = getattr(settings, 'CONFIG_CLASS', '')
    if config_cls_name:
        config_cls = import_object(config_cls_name)
    else:
        config_cls = Config
    return config_cls


def sys_exit(exitcode=None):
    """
    Exit from Python with exit code *exitcode*. If main process has children
    processes, exit immediately without cleaning. It is a workaround, because
    parent process waits for non-daemon children.
    """
    if multiprocessing.active_children():
        os._exit(exitcode)
    sys.exit(exitcode)


def main(args=None):
    """
    Run management command handled from command line.
    """
    # Base command line parser. Help is not allowed because command
    # line is parsed in two stages - in the first stage is found setting
    # module of the application, in the second stage are found management
    # command's arguments.
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        '-s', '--settings',
        dest='settings', action='store', type=str, default=None,
        help=_('application settings module')
    )

    # Get settings module
    try:
        settings = get_app_settings(parser, args)
    except ImportError as exc:
        parser.error(_("Invalid application settings module: {}").format(exc))

    # Get management commands and add their arguments into command
    # line parser
    commands = get_management_commands(settings)
    subparsers = parser.add_subparsers(
        dest='action', help=_('specify action')
    )
    for command_cls in six.itervalues(commands):
        subparser = subparsers.add_parser(
            command_cls.name, help=command_cls.help)
        for command_args, kwargs in command_cls.arguments:
            subparser.add_argument(*command_args, **kwargs)

    # Get config class and add its arguments into command line parser
    if settings:
        config_cls = get_config_class(settings)
        if not issubclass(config_cls, Config):
            raise TypeError(
                "Config class must be subclass of the "
                "shelter.core.config.Config")
        for config_args, kwargs in config_cls.arguments:
            parser.add_argument(*config_args, **kwargs)
    else:
        config_cls = Config

    # Add help argument and parse command line
    parser.add_argument(
        '-h', '--help', action='help',
        help=_('show this help message and exit')
    )
    cmdline_args = parser.parse_args(args)
    if not cmdline_args.action:
        parser.error(_('No action'))

    # Run management command
    command_cls = commands[cmdline_args.action]
    if command_cls.settings_required and not settings:
        parser.error(_(
            "Settings module is not defined. You must either set "
            "'SHELTER_SETTINGS_MODULE' environment variable or "
            "'-s/--settings' command line argument."
        ))
    try:
        config = config_cls(settings, cmdline_args)
    except ImproperlyConfiguredError as exc:
        parser.error(str(exc))
    command = command_cls(config)
    try:
        command()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        sys.stderr.flush()
        sys_exit(1)
    sys_exit(0)


if __name__ == '__main__':
    main()
