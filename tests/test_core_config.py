
import argparse
import importlib
import os.path

import pytest
import mock

from six.moves import configparser

from shelter.core.config import (
    get_conf_d_files, get_conf_files, get_configparser, Config
)
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


@mock.patch('shelter.core.config.logger')
def test_get_configparser(m, test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example.conf')
    conf_d_dir = os.path.join(test_conf_dir, 'example.conf.d')
    parser = get_configparser(conf_filename)
    assert isinstance(parser, configparser.RawConfigParser)
    assert parser.get('DEFAULT', 'test_option') == 'bar'
    expected = [
        mock.call.info("Found config '%s'", conf_filename),
        mock.call.info("Found config '%s'",
                       os.path.join(conf_d_dir, '10-app.conf')),
        mock.call.info("Found config '%s'",
                       os.path.join(conf_d_dir, '20-database.conf')),
    ]
    assert m.mock_calls == expected


@mock.patch('shelter.core.config.logger')
def test_get_configparser_empty_filename(m):
    parser = get_configparser('')
    assert isinstance(parser, configparser.RawConfigParser)
    assert m.mock_calls == []


@mock.patch('shelter.core.config.logger')
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
    conf_filename = os.path.join(test_conf_dir, 'example3.conf')
    with pytest.raises(ValueError) as e:
        get_configparser(conf_filename)
    assert 'is not a file' in str(e)


@mock.patch('shelter.core.config.logger')
@mock.patch('shelter.core.config.get_conf_d_files', new=lambda x: ['abc'])
def test_get_configparser_warn(m, test_conf_dir):
    conf_filename = os.path.join(test_conf_dir, 'example.conf')
    parser = get_configparser(conf_filename)
    assert isinstance(parser, configparser.RawConfigParser)
    assert parser.get('DEFAULT', 'test_option') == 'baz'
    expected = [
        mock.call.info("Found config '%s'", conf_filename),
        mock.call.info("Found config '%s'", 'abc'),
        mock.call.warning("Error while parsing config '%s'", 'abc'),
    ]
    assert m.mock_calls == expected


def test_config_cls():
    config = Config(1, 2, 3)
    assert "<shelter.core.config.Config: 0x" in repr(config)
    assert config.settings == 1
    assert config.config_parser == 2
    assert config.args_parser == 3


def test_config_context_class_default():
    config = Config(
        importlib.import_module('tests.settings1'),
        configparser.ConfigParser(),
        argparse.ArgumentParser()
    )
    assert config.context_class is Context


def test_config_context_class_user():
    config = Config(
        importlib.import_module('tests.settings2'),
        configparser.ConfigParser(),
        argparse.ArgumentParser()
    )
    assert config.context_class is not Context
    assert config.context_class is ContextTest


def test_config_interfaces(test_conf_dir):
    config_parser = configparser.ConfigParser()
    config_parser.read(os.path.join(test_conf_dir, 'example.conf'))
    config = Config(
        importlib.import_module('tests.settings1'),
        config_parser,
        argparse.ArgumentParser()
    )

    interfaces = sorted(config.interfaces, key=lambda x: x.name)

    assert len(interfaces) == 2

    assert interfaces[0].name == 'fastrpc'
    assert interfaces[0].host == '192.168.1.0'
    assert interfaces[0].port == 4445
    assert len(interfaces[0].urls) == 0

    assert interfaces[1].name == 'http'
    assert interfaces[1].host == ''
    assert interfaces[1].port == 4444
    assert len(interfaces[1].urls) == 2
