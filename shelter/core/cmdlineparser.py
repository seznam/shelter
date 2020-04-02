"""
Command line parser helpers.
"""

import argparse
import sys

from gettext import gettext as _


def argument(*args, **kwargs):
    """
    Return tuple containig all positional arguments as :class:`!tuple`
    and all named arguments as :class:`!dict`. *args* and *kwargs* have
    the same meaning as a :meth:`ArgumentParser.add_argument
    <argparse.ArgumentParser.add_argument>` method.

    .. code-block:: python

        >>> argument('-f', '--file', action='store', type=str, default='')
        (('-f', '--file'), {action: 'store', type: str, default: ''})
    """
    return args, kwargs


class ArgumentParser(argparse.ArgumentParser):
    """
    Extends :class:`ArgumentParser` from Python's standard library.
    Overrides how the error messages are printed.
    """

    def error(self, message):
        """
        Print on **stderr** error message from command line parser and
        exit process.
        """
        self.print_help(sys.stderr)
        self.exit(2, _('\n{:s}: error: {:s}\n').format(self.prog, message))
