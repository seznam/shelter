"""
Module :module:`shelter.core.app` provides functions for initializing
Tornado's application.
"""

import tornado.web

from shelter.core.web import NullHandler

__all__ = ['get_tornado_apps']


def get_tornado_apps(context, debug=False):
    """
    Create Tornado's application for all interfaces which are defined
    in the configuration. *context* is instance of the
    :class:`shelter.core.context.Context`. If *debug* is :const:`True`,
    server will be run in **DEBUG** mode. Return :class:`list` of the
    :class:`tornado.web.Application` instances.
    """
    apps = []
    for interface in context.config.interfaces:
        urls = interface.urls
        if not urls:
            urls = [tornado.web.URLSpec('/', NullHandler)]
        for url in urls:
            url.kwargs['context'] = context
            url.kwargs['interface'] = interface
        apps.append(
            tornado.web.Application(
                urls, debug=debug, context=context, interface=interface))
    return apps
