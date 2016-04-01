
from tornado.web import URLSpec

from shelter.core.web import NullHandler


urls_http = (
    URLSpec('/baz/', NullHandler),
    URLSpec('/bar/', NullHandler),
)
