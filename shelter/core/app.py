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
            # There is change in implementation of tornado.web.URLSpec.
            # From Tornado 4.5 we have to use target_kwargs property
            # of base class of tornado.web.URLSpec: tornado.routing.Rule.
            if hasattr(url, 'target_kwargs'):
                # We have newer version of Tornado
                url.target_kwargs['context'] = context
                url.target_kwargs['interface'] = interface
                url.kwargs = {}
            # Always do it old way
            url.kwargs['context'] = context
            url.kwargs['interface'] = interface
        apps.append(
            tornado.web.Application(
                urls, debug=debug, context=context, interface=interface))
    return apps
