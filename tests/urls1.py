
from tornado.web import URLSpec

from shelter.core.web import NullHandler


urls_http = (
    URLSpec('/baz/', NullHandler),
    URLSpec('/bar/', NullHandler),
)


urls_unix = (
    URLSpec('/baz/', NullHandler),
    URLSpec('/bar/', NullHandler),
    URLSpec('/foo/', NullHandler),
)
