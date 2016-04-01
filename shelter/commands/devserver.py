"""
Run development server.
"""

import tornado.ioloop
import tornado.netutil
import tornado.httpserver

from shelter.core.app import get_tornado_apps
from shelter.core.commands import BaseCommand


class DevServer(BaseCommand):
    """
    Management command which runs development server. Server is run in
    DEBUG mode.
    """

    name = 'devserver'
    help = 'run server for local development'

    def command(self):
        # For each interface create Tornado application and start to
        # listen on the port.
        listen_on = []
        for app in get_tornado_apps(self.context, debug=True):
            interface = app.settings['interface']
            host, port = interface.host, interface.port
            sockets = tornado.netutil.bind_sockets(port, address=host)

            server = tornado.httpserver.HTTPServer(app)
            server.add_sockets(sockets)

            listen_on.append("{:s}:{:d}".format(host, port))

        # Run IOLoop
        if listen_on:
            self.stdout.write(
                "Start server on %s, press Ctrl+C to stop\n" %
                ", ".join(listen_on)
            )
            self.stdout.flush()

            tornado.ioloop.IOLoop.instance().start()
