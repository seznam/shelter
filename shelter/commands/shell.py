"""
Run Python's interactive console.
"""

from shelter.core.commands import BaseCommand


class Shell(BaseCommand):
    """
    Management command which runs interactive Python's shell, either
    **IPython** or **python**.
    """

    name = 'shell'
    help = 'runs a python interactive interpreter'

    def command(self):
        user_ns = {
            'context': self.context,
        }
        try:
            import IPython
            IPython.start_ipython(argv=[], user_ns=user_ns)
        except ImportError:
            import code
            code.interact(local=user_ns)

    def _configure_logging(self):
        """
        Do not configure logging.
        """
        pass
