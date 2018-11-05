
import mock

import tornado.web

from shelter.core.config import Config
from shelter.core.web import BaseRequestHandler, NullHandler


def test_base_request_handler():
    app = tornado.web.Application([], context=1, interface=2)
    req = mock.Mock()

    h = BaseRequestHandler(app, req)

    assert h.context == 1
    assert h.interface == 2


def test_null_handler():
    app = tornado.web.Application(
        [], context=object(), interface=Config.Interface(
            name='foo', host='', port=1, unix_socket=None,
            processes=0, urls=[]
        )
    )
    req = mock.Mock()

    with mock.patch.object(NullHandler, 'write') as m_write:
        with mock.patch.object(NullHandler, 'set_header') as m_set_header:
            h = NullHandler(app, req)
            h.get()

    m_write.assert_called_once_with("Interface 'foo' works!\n")
    m_set_header.assert_called_once_with(
        "Content-Type", "text/plain; charset=UTF-8")
