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
    service_processes_start = True
    service_processes_in_thread = True

    def command(self):
        # For each interface create Tornado application and start to
        # listen on the port.
        listen_on = []
        for app in get_tornado_apps(self.context, debug=True):
            interface = app.settings['interface']

            if not interface.port and not interface.unix_socket:
                raise ValueError(
                    'Interface MUST listen either on TCP '
                    'or UNIX socket or both')

            server = tornado.httpserver.HTTPServer(app)

            sockets = []
            if interface.port:
                host, port = interface.host, interface.port
                sockets.extend(
                    tornado.netutil.bind_sockets(port, address=host))
                listen_on.append(
                    "{:s}:{:d}".format(host, port))
            if interface.unix_socket:
                sockets.append(
                    tornado.netutil.bind_unix_socket(interface.unix_socket))
                listen_on.append(
                    "{:s}".format(interface.unix_socket))
            server.add_sockets(sockets)

        # Run IOLoop
        if listen_on:
            self.stdout.write(
                "Start dev server on %s, press Ctrl+C to stop\n" %
                ", ".join(listen_on)
            )
            self.stdout.flush()

            try:
                tornado.ioloop.IOLoop.instance().start()
            except KeyboardInterrupt:
                tornado.ioloop.IOLoop.instance().add_callback(
                    tornado.ioloop.IOLoop.instance().stop)
