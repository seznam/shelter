"""
Module :module:`shelter.core.web` provides an ancestor for HTTP handlers.
"""

import six

from tornado.web import RequestHandler

from shelter.utils.logging import AddLoggerMeta

__all__ = ['BaseRequestHandler']


class BaseRequestHandler(six.with_metaclass(AddLoggerMeta, RequestHandler)):
    """
    Base class for HTTP handlers, overrides
    :class:`tornado.web import RequestHandler`. Adds *logger* attribute
    with Python's logger instance, *context* with
    :class:`shelter.core.context.Context` instance and *interface* with
    :class:`shelter.core.config.Config.Interface` instance with definition
    of the interface.
    """

    def initialize(self, **kwargs):
        self.context = kwargs['context']
        self.interface = kwargs['interface']


class NullHandler(BaseRequestHandler):
    """
    HTTP Handler for '/' when not defined any url to handler route.
    """

    def get(self):
        self.write("Interface '%s' works!\n" % self.interface.name)
        self.set_header("Content-Type", 'text/plain; charset=UTF-8')
