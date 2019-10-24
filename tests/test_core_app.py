
import importlib

import tornado.web

from shelter.core.app import get_tornado_apps
from shelter.core.cmdlineparser import ArgumentParser
from shelter.core.config import Config
from shelter.core.context import Context


class ApplicationTest(tornado.web.Application):

    pass


def test_get_tornado_apps():
    config = Config(
        importlib.import_module('tests.settings1'),
        ArgumentParser()
    )
    context = config.context_class.from_config(config)

    apps = sorted(
        get_tornado_apps(context), key=lambda x: x.settings['interface'].name)

    assert len(apps) == 4

    assert isinstance(apps[0].settings['context'], Context)
    assert isinstance(apps[0].settings['interface'], Config.Interface)
    assert apps[0].settings['interface'].name == 'fastrpc'
    assert type(apps[0]) is tornado.web.Application

    assert isinstance(apps[1].settings['context'], Context)
    assert isinstance(apps[1].settings['interface'], Config.Interface)
    assert apps[1].settings['interface'].name == 'http'
    assert type(apps[1]) is tornado.web.Application

    assert isinstance(apps[2].settings['context'], Context)
    assert isinstance(apps[2].settings['interface'], Config.Interface)
    assert apps[2].settings['interface'].name == 'rest'
    assert type(apps[2]) is ApplicationTest

    assert isinstance(apps[3].settings['context'], Context)
    assert isinstance(apps[3].settings['interface'], Config.Interface)
    assert apps[3].settings['interface'].name == 'unix'
    assert type(apps[3]) is ApplicationTest
