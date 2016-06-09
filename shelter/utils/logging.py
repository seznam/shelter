"""
Helpers for Python's logging.
"""

from __future__ import absolute_import

import logging

__all__ = ['AddLoggerMeta']


BASE_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'default': {
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'NOTSET',
            'formatter': 'default',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


class AddLoggerMeta(type):
    """
    Metaclass which adds *logger* attribule into class. Name of the logger
    is **module.path.MyClass**.
    """

    def __new__(mcs, name, bases, kwattrs):
        logger_name = "{:s}.{:s}".format(kwattrs['__module__'], name)
        kwattrs['logger'] = logging.getLogger(logger_name)
        return super(AddLoggerMeta, mcs).__new__(mcs, name, bases, kwattrs)
