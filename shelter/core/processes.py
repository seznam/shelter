"""
Module :module:`shelter.core.processes` provides an ancestor and
functionality for writing service processes.
"""

import ctypes
import logging
import multiprocessing
import os
import signal
import time

import setproctitle

from shelter.core.constants import SERVICE_PROCESS

__all__ = ['BaseProcess']


class BaseProcess(multiprocessing.Process):
    """
    Ancestor for service processes. Adjust :attribute:`interval` attribute
    and override method :meth:`loop` which is repeatedly called every
    :attribute:`interval` seconds.
    """

    interval = 0
    """
    Interval in seconds. After this time :meth:`loop` method is
    repeatedly called.
    """

    def __init__(self, context):
        super(BaseProcess, self).__init__()

        self._parent_pid = os.getpid()
        self._ready = multiprocessing.Value(ctypes.c_bool, False)
        self._stop_event = multiprocessing.Event()

        self.context = context
        self.logger = logging.getLogger(
            "{:s}.{:s}".format(__name__, self.__class__.__name__))

        self.initialize()

    def initialize(self):
        """
        Initialize instance attributes. You can override this method in
        the subclasses.
        """
        pass

    @property
    def ready(self):
        """
        :const:`True` when service process has been started successfully,
        else :const:`False`.
        """
        return self._ready.value

    def stop(self):
        """
        Set stop flag. :meth:`run` method checks this flag and if it is
        :const:`True`, service process will be stopped.
        """
        self._stop_event.set()

    def run(self):
        """
        Child process. Repeatedly call :meth:`loop` method every
        :attribute:`interval` seconds.
        """
        setproctitle.setproctitle("{:s}: {:s}".format(
            self.context.config.name, self.__class__.__name__))
        self.logger.info(
            "Worker '%s' has been started with pid %d",
            self.__class__.__name__, os.getpid())

        # Register SIGINT handler which will exit service process
        def sigint_handler(unused_signum, unused_frame):
            """
            Exit service process when SIGINT is reached.
            """
            self.stop()
        signal.signal(signal.SIGINT, sigint_handler)

        # Initialize logging
        self.context.config.configure_logging()
        # Initialize child
        self.context.initialize_child(SERVICE_PROCESS, process=self)

        next_loop_time = 0
        while 1:
            # Exit if pid of the parent process has changed (parent process
            # has exited and init is new parent) or if stop flag is set.
            if os.getppid() != self._parent_pid or self._stop_event.is_set():
                break
            # Repeatedly call loop method. After first call set ready flag.
            if time.time() >= next_loop_time:
                try:
                    self.loop()
                except Exception:
                    self.logger.exception(
                        "Worker '%s' failed", self.__class__.__name__)
                else:
                    if not next_loop_time and not self.ready:
                        self._ready.value = True
                next_loop_time = time.time() + self.interval
            else:
                time.sleep(0.25)

    def loop(self):
        """
        Repeatedly in interval :attribute:`interval` do code in this
        method. It is an abstract method, override it in subclasses.
        """
        raise NotImplementedError
