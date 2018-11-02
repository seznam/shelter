"""
Show effective configuration.
"""

from pprint import pformat

from shelter.core.commands import BaseCommand


class ShowConfig(BaseCommand):
    """
    Management command which shows effective configuration.
    """

    name = 'showconfig'
    help = 'show effective configuration'

    def command(self):
        for k, value in self.context.config.get_config_items():
            self.stdout.write("{}: {}\n".format(k, pformat(value)))
            self.stdout.flush()
