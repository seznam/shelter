
import argparse
import importlib

from six.moves import configparser

from shelter.core.app import get_tornado_apps
from shelter.core.config import Config
from shelter.core.context import Context


def test_get_tornado_apps():
    config = Config(
        importlib.import_module('tests.settings1'),
        configparser.ConfigParser(),
        argparse.ArgumentParser()
    )
    context = config.context_class.from_config(config)

    apps = sorted(
        get_tornado_apps(context), key=lambda x: x.settings['interface'].name)

    assert len(apps) == 2

    assert isinstance(apps[0].settings['context'], Context)
    assert isinstance(apps[0].settings['interface'], Config.Interface)
    assert apps[0].settings['interface'].name == 'fastrpc'

    assert isinstance(apps[1].settings['context'], Context)
    assert isinstance(apps[1].settings['interface'], Config.Interface)
    assert apps[1].settings['interface'].name == 'http'
