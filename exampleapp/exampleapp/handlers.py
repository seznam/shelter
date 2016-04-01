
from shelter.core.web import BaseRequestHandler


class ShowValueHandler(BaseRequestHandler):

    def compute_etag(self):
        return None

    def get(self):
        self.write("Current value: %s" % self.context.value)
