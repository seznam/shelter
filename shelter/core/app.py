"""
Module :module:`shelter.core.app` provides functions for initializing
Tornado's application.
"""

import tornado.web

from shelter.core.web import NullHandler
from shelter.utils.imports import import_object

__all__ = ['get_tornado_apps']


def get_tornado_apps(context, debug=False):
    """
    Create Tornado's application for all interfaces which are defined
    in the configuration. *context* is instance of the
    :class:`shelter.core.context.Context`. If *debug* is :const:`True`,
    server will be run in **DEBUG** mode. Return :class:`list` of the
    :class:`tornado.web.Application` instances.
    """
    if context.config.app_settings_handler:
        app_settings_handler = import_object(
            context.config.app_settings_handler)
        settings = app_settings_handler(context)
    else:
        settings = {}

    apps = []
    for interface in context.config.interfaces:
        urls = interface.urls
        if not urls:
            urls = [tornado.web.URLSpec('/', NullHandler)]
        apps.append(
            tornado.web.Application(
                urls, debug=debug, context=context,
                interface=interface, **settings
            )
        )
    return apps
