"""
Modul :module:`shelter.main` is an entry point from command line into
**Shelter** application.
"""

import argparse
import importlib
import itertools
import os

from gettext import gettext as _

from shelter.commands import SHELTER_MANAGEMENT_COMMANDS
from shelter.core.commands import BaseCommand
from shelter.core.config import get_configparser, Config
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
    else:
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
    Podle nastaveni **settings.CONFIG_CLASS** vrat tridu nesouci
    konfiguraci aplikace, nebo vychozi :class:`shelter.core.config.Config`
    pokud neni definovano.
    """
    config_cls_name = getattr(settings, 'CONFIG_CLASS', '')
    if config_cls_name:
        config_cls = import_object(config_cls_name)
    else:
        config_cls = Config
    return config_cls


def parser_error(parser, message):
    """
    Print on **stderr** error message from command line parser and
    exit process.
    """
    parser.print_help()
    parser.exit(2, _('\n{:s}: error: {:s}\n').format(parser.prog, message))


def main(args=None):
    """
    Run management command handled from command line.
    """
    # Base command line parser. Help is not allowed because command
    # line is parsed in two stages - in the first stage is found setting
    # module of the application, in the second stage are found management
    # command's arguments.
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument(
        '-s', '--settings',
        dest='settings', action='store', type=str, default=None,
        help=_('application settings module')
    )
    parser.add_argument(
        '-f', '--config-file',
        dest='config', action='store', type=str, default=None,
        help=_('configuration file')
    )

    # Get settings module
    try:
        settings = get_app_settings(parser, args)
    except ImportError as ex:
        parser_error(
            parser,
            _("Invalid application settings module: %s") % ex
        )

    # Get management commands and add their arguments into command
    # line parser
    commands = get_management_commands(settings)
    subparsers = parser.add_subparsers(
        dest='action', help=_('specify action')
    )
    for command_cls in commands.values():
        subparser = subparsers.add_parser(
            command_cls.name, help=command_cls.help)
        for command_args, kwargs in command_cls.arguments:
            subparser.add_argument(*command_args, **kwargs)

    # Add help and parse command line
    parser.add_argument(
        '-h', '--help', action='help',
        help=_('show this help message and exit')
    )
    cmdline_args = parser.parse_args(args)
    if not cmdline_args.action:
        parser_error(parser, _('No action'))

    # Get configuration file parser
    config_parser = get_configparser(cmdline_args.config)

    # Run management command
    command_cls = commands[cmdline_args.action]
    if command_cls.settings_required:
        if not settings:
            parser_error(
                parser, _(
                    "Settings module is not defined. You must either set "
                    "'SHELTER_SETTINGS_MODULE' environment variable or "
                    "'-s/--settings' command line argument."
                )
            )
        config_cls = get_config_class(settings)
        if not issubclass(config_cls, Config):
            raise TypeError(
                "Config class must be subclass of the "
                "shelter.core.config.Config")
        config = config_cls(settings, config_parser, cmdline_args)
    else:
        config = Config(None, config_parser, cmdline_args)
    command = command_cls(config)
    command()


if __name__ == '__main__':
    main()
