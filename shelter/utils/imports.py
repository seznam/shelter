"""
Helpers for importing Python's modules.
"""

import importlib

__all__ = ['import_object']


def import_object(name):
    """
    Import module and return object from it. *name* is :class:`str` in
    format ``module.path.ObjectClass``.

    ::
        >>> import_command('module.path.ObjectClass')
        <class 'module.path.ObjectClass'>
    """
    parts = name.split('.')
    if len(parts) < 2:
        raise ValueError("Invalid name '%s'" % name)
    module_name = ".".join(parts[:-1])
    obj_name = parts[-1]
    module = importlib.import_module(module_name)
    return getattr(module, obj_name)
