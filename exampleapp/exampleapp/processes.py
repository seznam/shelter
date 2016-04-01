
import base64
import os

from shelter.core.processes import BaseProcess


class WarmCache(BaseProcess):

    interval = 10

    def loop(self):
        self.context.value = base64.b64encode(os.urandom(6))
