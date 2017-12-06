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

            if interface.port and interface.unix_socket:
                raise ValueError(
                    'Interface MUST NOT listen on both TCP and UNIX socket')
            elif interface.port:
                host, port = interface.host, interface.port
                sockets = tornado.netutil.bind_sockets(port, address=host)

                server = tornado.httpserver.HTTPServer(app)
                server.add_sockets(sockets)

                listen_on.append("{:s}:{:d}".format(host, port))
            elif interface.unix_socket:
                server = tornado.httpserver.HTTPServer(app)
                socket = tornado.netutil.bind_unix_socket(
                    interface.unix_socket)
                server.add_socket(socket)
                listen_on.append("{:s}".format(interface.unix_socket))
            else:
                raise ValueError(
                    'Interface MUST listen either on TCP or UNIX socket')

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
