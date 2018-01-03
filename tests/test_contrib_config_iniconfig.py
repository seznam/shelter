
import importlib
import os.path

from shelter.core.cmdlineparser import ArgumentParser

import pytest
import mock

from six.moves import configparser

from shelter.contrib.config.iniconfig import (
    get_conf_d_files, get_conf_files, get_configparser, IniConfig
)
from shelter.core.exceptions import ImproperlyConfiguredError
from shelter.core.context import Context


class ContextTest(Context):
    pass


@pytest.fixture
def test_conf_dir():
    return os.path.join(os.path.dirname(__file__), 'conf')


def test_get_conf_d_files(test_conf_dir):
    conf_d_dir = os.path.join(test_conf_dir, 'example.conf.d')
    expected = [
        os.path.join(conf_d_dir, '10-app.conf'),
        os.path.join(conf_d_dir, '20-database.conf'),
    ]
    assert get_conf_d_files(conf_d_dir) == expected


def test_get_conf_d_files_fail_when_not_a_directory(test_conf_dir):
    with pytest.raises(ValueError) as e:
        get_conf_d_files(os.path.join(test_conf_dir, 'foo'))
    assert 'is not a directory' in str(e)


def test_get_conf_files(test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example.conf')
    conf_d_dir = os.path.join(test_conf_dir, 'example.conf.d')
    expected = [
        conf_filename,
        os.path.join(conf_d_dir, '10-app.conf'),
        os.path.join(conf_d_dir, '20-database.conf'),
    ]
    assert get_conf_files(conf_filename) == expected


def test_get_conf_files_fail_when_not_a_file(test_conf_dir):
    with pytest.raises(ValueError) as e:
        get_conf_files(os.path.join(test_conf_dir, 'foo.conf'))
    assert 'is not a file' in str(e)


@mock.patch('shelter.contrib.config.iniconfig.logger')
def test_get_configparser(m, test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example.conf')
    conf_d_dir = os.path.join(test_conf_dir, 'example.conf.d')
    parser = get_configparser(conf_filename)
    assert isinstance(parser, configparser.RawConfigParser)
    assert parser.get('DEFAULT', 'test_option') == 'bar'
    assert m.mock_calls == [
        mock.call.info("Found config '%s'", conf_filename),
        mock.call.info("Found config '%s'",
                       os.path.join(conf_d_dir, '10-app.conf')),
        mock.call.info("Found config '%s'",
                       os.path.join(conf_d_dir, '20-database.conf')),
    ]


def test_get_configparser_empty_filename():
    with pytest.raises(ImproperlyConfiguredError) as exc_info:
        get_configparser('')
    assert "Configuration file is not defined" in str(exc_info.value)


@mock.patch('shelter.contrib.config.iniconfig.logger')
def test_get_configparser_no_conf_d_dir(m, test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example2.conf')
    parser = get_configparser(conf_filename)
    assert isinstance(parser, configparser.RawConfigParser)
    assert parser.get('DEFAULT', 'test_option') == 'baz'
    expected = [
        mock.call.info("Found config '%s'", conf_filename),
    ]
    assert m.mock_calls == expected


def test_get_configparser_config_does_not_exist(test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example_not_exists.conf')
    with pytest.raises(ValueError) as e:
        get_configparser(conf_filename)
    assert 'is not a file' in str(e)


@mock.patch('shelter.contrib.config.iniconfig.logger')
@mock.patch(
    'shelter.contrib.config.iniconfig.get_conf_d_files', new=lambda x: ['abc'])
def test_get_configparser_warn(m, test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example.conf')
    parser = get_configparser(conf_filename)
    assert isinstance(parser, configparser.RawConfigParser)
    assert parser.get('DEFAULT', 'test_option') == 'baz'
    assert m.mock_calls == [
        mock.call.info("Found config '%s'", conf_filename),
        mock.call.info("Found config '%s'", 'abc'),
        mock.call.warning("Error while parsing config '%s'", 'abc'),
    ]


def test_config_interfaces(test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example.conf')
    parser = ArgumentParser()
    parser.add_argument('-f', dest='config')
    config = IniConfig(importlib.import_module('tests.settings1'),
                       parser.parse_args(['-f', conf_filename]))

    interfaces = sorted(config.interfaces, key=lambda x: x.name)

    assert len(interfaces) == 3

    assert interfaces[0].name == 'fastrpc'
    assert interfaces[0].host == '192.168.1.0'
    assert interfaces[0].port == 4445
    assert interfaces[0].unix_socket is None
    assert len(interfaces[0].urls) == 0

    assert interfaces[1].name == 'http'
    assert interfaces[1].host == ''
    assert interfaces[1].port == 4444
    assert interfaces[1].unix_socket is None
    assert len(interfaces[1].urls) == 2

    assert interfaces[2].name == 'unix'
    assert interfaces[2].host is None
    assert interfaces[2].port is None
    assert interfaces[2].unix_socket == '/tmp/tornadoini.socket'
    assert len(interfaces[2].urls) == 3


def test_config_interfaces_both_tcp_and_unix(test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example5.conf')
    parser = ArgumentParser()
    parser.add_argument('-f', dest='config')
    config = IniConfig(importlib.import_module('tests.settings5'),
                       parser.parse_args(['-f', conf_filename]))

    interface = config.interfaces[0]

    assert interface.name == 'http_both_tcp_and_unix'
    assert interface.host == ''
    assert interface.port == 4444
    assert interface.unix_socket == '/tmp/tornadoini.socket'


def test_config_interfaces_fail_when_neither_tcp_nor_unix(test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example6.conf')
    with pytest.raises(ValueError) as e:
        parser = ArgumentParser()
        parser.add_argument('-f', dest='config')
        config = IniConfig(importlib.import_module('tests.settings6'),
                           parser.parse_args(['-f', conf_filename]))
        _ = config.interfaces
    assert "Interface MUST listen either on TCP or UNIX socket" in str(e)
