
import importlib

import pytest

from shelter.core.cmdlineparser import ArgumentParser
from shelter.core.config import Config
from shelter.core.context import Context


class ContextTest(Context):
    pass


def test_config_cls():
    config = Config(1, 2)
    assert "<shelter.core.config.Config: 0x" in repr(config)
    assert config.settings == 1
    assert config.args_parser == 2


def test_config_context_class_default():
    config = Config(
        importlib.import_module('tests.settings1'),
        ArgumentParser()
    )
    assert config.context_class is Context


def test_config_context_class_user():
    config = Config(
        importlib.import_module('tests.settings2'),
        ArgumentParser()
    )
    assert config.context_class is not Context
    assert config.context_class is ContextTest


def test_config_interfaces():
    config = Config(
        importlib.import_module('tests.settings1'),
        ArgumentParser()
    )

    interfaces = sorted(config.interfaces, key=lambda x: x.name)

    assert len(interfaces) == 3

    assert interfaces[0].name == 'fastrpc'
    assert interfaces[0].host == '192.168.1.0'
    assert interfaces[0].port == 4445
    assert len(interfaces[0].urls) == 0

    assert interfaces[1].name == 'http'
    assert interfaces[1].host == ''
    assert interfaces[1].port == 4443
    assert len(interfaces[1].urls) == 2

    assert interfaces[2].name == 'unix'
    assert interfaces[2].host is None
    assert interfaces[2].port is None
    assert interfaces[2].unix_socket == '/tmp/tornado.socket'
    assert len(interfaces[2].urls) == 3


def test_config_interfaces_both_tcp_and_unix():
    config = Config(
        importlib.import_module('tests.settings5'),
        ArgumentParser()
    )

    interface = config.interfaces[0]

    assert interface.name == 'http_both_tcp_and_unix'
    assert interface.host == ''
    assert interface.port == 4443
    assert interface.unix_socket == '/tmp/tornado.socket'


def test_config_interface_fail_when_neither_tcp_nor_unix():
    config = Config(
        importlib.import_module('tests.settings6'),
        ArgumentParser()
    )

    with pytest.raises(ValueError) as e:
        _ = config.interfaces
    assert "Interface MUST listen either on TCP or UNIX socket" in str(e)
