
from tornado.web import URLSpec

from shelter.core.web import NullHandler

from exampleapp.handlers import ShowValueHandler


urls_default = (
    URLSpec(r'/', NullHandler),
    URLSpec(r'/value/', ShowValueHandler),
)
