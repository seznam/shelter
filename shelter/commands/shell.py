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
    service_processes_start = True
    service_processes_in_thread = True

    def command(self):
        self.context.config._debug = True

        user_ns = {
            'context': self.context,
        }
        try:
            import IPython
            IPython.start_ipython(argv=[], user_ns=user_ns)
        except ImportError:
            import code
            code.interact(local=user_ns)
