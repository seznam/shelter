"""
Show effective configuration.
"""

import six

from shelter.core.commands import BaseCommand


class ShowConfig(BaseCommand):
    """
    Management command which shows effective configuration from
    all configuration files.
    """

    name = 'showconfig'
    help = 'show effective configuration file'

    def command(self):
        f_config = six.StringIO()
        self.context.config.config_parser.write(f_config)
        self.stdout.write(f_config.getvalue())
        self.stdout.flush()
