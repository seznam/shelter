
from shelter.core.web import BaseRequestHandler


class ShowValueHandler(BaseRequestHandler):

    def compute_etag(self):
        return None

    def get(self):
        """Returns current value from internal context
        ---
        tags: [value]
        summary: Get current value
        description: Get the current value from internal context

        responses:
            200:
                description: Message with the current value
                content:
                    text/plain:
                        schema:
                            type: string
        """
        self.write("Current value: %s" % self.context.value)
