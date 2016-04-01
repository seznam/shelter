"""
Run production server.
"""

import functools
import multiprocessing
import os
import signal
import sys

import setproctitle
import six

import tornado.httpserver
import tornado.ioloop
import tornado.netutil
import tornado.process

from shelter.core.app import get_tornado_apps
from shelter.core.commands import BaseCommand
from shelter.core.processes import Worker, start_workers
from shelter.utils.logging import configure_logging


def stop_child(http_server, parent_pid):
    """
    Tornado's callback function which checks PID of the parent process.
    If PID of the parent process is changed (parent has stopped), will
    stop **IOLoop**.
    """
    if os.getppid() != parent_pid:
        # Stop HTTP server (stop accept new requests)
        http_server.stop()
        # Stop IOLoop
        tornado.ioloop.IOLoop.instance().add_callback(
            tornado.ioloop.IOLoop.instance().stop)


def tornado_worker(tornado_app, sockets, parent_pid):
    """
    Tornado worker which process HTTP requests.
    """
    setproctitle.setproctitle(
        "{:s}: worker {:s}".format(
            tornado_app.settings['context'].config.name,
            tornado_app.settings['interface'].name
        )
    )

    configure_logging(tornado_app.settings['context'].config)

    # Run HTTP server
    http_server = tornado.httpserver.HTTPServer(tornado_app)
    http_server.add_sockets(sockets)

    # Register SIGINT handler which will stop worker
    def sigint_handler(dummy_signum, dummy_frame):
        """
        Stop HTTP server and IOLoop if SIGINT.
        """
        # Stop HTTP server (stop accept new requests)
        http_server.stop()
        # Stop IOLoop
        tornado.ioloop.IOLoop.instance().add_callback(
            tornado.ioloop.IOLoop.instance().stop)
    signal.signal(signal.SIGINT, sigint_handler)

    # Register job which will stop worker if parent process PID is changed
    stop_callback = tornado.ioloop.PeriodicCallback(
        functools.partial(stop_child, http_server, parent_pid), 250)
    stop_callback.start()

    # Run IOLoop
    tornado.ioloop.IOLoop.instance().start()


def get_worker_instance(args):
    """
    Create and run worker. Return instance of the
    :class:`multiprocessing.Process`.
    """
    inst = multiprocessing.Process(target=tornado_worker, args=args)
    inst.ready = True
    return inst


class RunServer(BaseCommand):
    """
    Management command which runs production server.
    """

    name = 'runserver'
    help = 'run server'
    service_processes_start = True
    service_processes_in_thread = False

    def command(self):
        setproctitle.setproctitle(
            "{:s}: master process '{:s}'".format(
                self.context.config.name, " ".join(sys.argv)
            ))
        # For each interface create workers
        for tornado_app in get_tornado_apps(self.context, debug=False):
            self.init_workers(tornado_app)
        # Run workers
        start_workers(self.workers, max_restarts=100)

    def init_workers(self, tornado_app):
        """
        For Tornado's application *tornado_app* create workers instances
        and add them into list of the management command processes.
        """
        processes = tornado_app.settings['interface'].processes
        if processes <= 0:
            processes = tornado.process.cpu_count()

        self.logger.info(
            "Init %d worker(s) for interface '%s'",
            processes, tornado_app.settings['interface'].name)

        sockets = tornado.netutil.bind_sockets(
            tornado_app.settings['interface'].port,
            address=tornado_app.settings['interface'].host)
        for dummy_i in six.moves.range(processes):
            self.workers.append(
                Worker(
                    name=tornado_app.settings['interface'].name,
                    factory=get_worker_instance,
                    args=(tornado_app, sockets, self.pid)
                )
            )
