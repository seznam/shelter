
import mock

from shelter.core.config import Config
from shelter.core.web import BaseRequestHandler, NullHandler


def test_base_request_handler():
    with mock.patch.object(BaseRequestHandler, '__init__', return_value=None):
        h = BaseRequestHandler()
        h.initialize(context=1, interface=2)
    assert h.context == 1
    assert h.interface == 2


def test_null_handler():
    with mock.patch.object(NullHandler, '__init__', return_value=None), \
         mock.patch.object(NullHandler, 'write') as m_write, \
         mock.patch.object(NullHandler, 'set_header') as m_set_header:
        h = NullHandler()
        h.initialize(
            context=object(),
            interface=Config.Interface('foo', '', 1, 0, [])
        )
        h.get()

    m_write.assert_called_once_with("Interface 'foo' works!\n")
    m_set_header.assert_called_once_with(
        "Content-Type", "text/plain; charset=UTF-8")
