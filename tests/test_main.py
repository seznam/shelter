
import mock
import pytest

import shelter.main

from shelter.core.cmdlineparser import argument
from shelter.core.commands import BaseCommand
from shelter.commands.startproject import StartProject
from shelter.core.config import Config


class Cmd(BaseCommand):

    name = 'testcmd'
    help = 'test cmd help text'
    arguments = (
        argument('--name', dest='name', help='your name'),
    )


class CmdBadType(object):
    pass


class AppConfig(Config):
    pass


class AppConfigBadType(object):
    pass


@mock.patch.object(BaseCommand, 'command')
def test_main(m):
    with pytest.raises(SystemExit) as e:
        shelter.main.main(['-s', 'tests.settings1', 'testcmd'])
    m.assert_called_once_with()
    assert e.value.code == 0


def test_main_exit_when_no_settings_module():
    with pytest.raises(SystemExit) as e:
        shelter.main.main(['shell'])
    assert e.value.code == 2


def test_main_fail_when_settings_does_not_exist():
    with pytest.raises(SystemExit) as e:
        shelter.main.main(['-s', 'tests.settings', 'testcmd'])
    assert e.value.code == 2


def test_main_default_config_class():

    def command(self):
        assert type(self.context.config) == Config

    with mock.patch.object(BaseCommand, 'command', new=command):
        with pytest.raises(SystemExit) as e:
            shelter.main.main(['-s', 'tests.settings1', 'testcmd'])
        assert e.value.code == 0


def test_main_default_config_class_when_settings_is_not_required():

    def command(self):
        assert type(self.context.config) == Config

    with mock.patch.object(StartProject, 'command', new=command):
        with pytest.raises(SystemExit) as e:
            shelter.main.main(['startproject', 'foo'])
        assert e.value.code == 0


def test_main_custom_config_class():

    def command(self):
        assert type(self.context.config) == AppConfig

    with mock.patch.object(BaseCommand, 'command', new=command):
        with pytest.raises(SystemExit) as e:
            shelter.main.main(['-s', 'tests.settings3', 'testcmd'])
        assert e.value.code == 0


def test_main_custom_config_class_bad_type():
    with pytest.raises(TypeError) as e:
        shelter.main.main(['-s', 'tests.settings4', 'testcmd'])
    assert "must be subclass of the shelter.core.config.Config" in str(e)


def test_main_fail_when_invalid_command_subclass():
    with pytest.raises(ValueError) as e:
        shelter.main.main(['-s', 'tests.settings2', 'testcmd'])
    assert "is not subclass of the BaseCommand" in str(e)


def test_main_exit_when_no_action():
    with pytest.raises(SystemExit) as e:
        shelter.main.main(['-s', 'tests.settings1'])
    assert e.value.code == 2


@mock.patch.object(BaseCommand, 'command')
def test_main_fail_when_command_error(m):
    m.side_effect = [KeyError]
    with pytest.raises(SystemExit) as e:
        shelter.main.main(['-s', 'tests.settings1', 'testcmd'])
    m.assert_called_once_with()
    assert e.value.code == 1


@mock.patch.object(BaseCommand, 'command')
def test_main_force_exit_when_children(m_command):
    m_command.side_effect = [KeyError]
    with mock.patch('shelter.main.multiprocessing') as m_multiprocessing:
        m_multiprocessing.active_children.return_value = [mock.Mock()]
        with mock.patch('os._exit') as m_os_exit:
            m_os_exit.side_effect = [SystemExit]
            with pytest.raises(SystemExit):
                shelter.main.main(['-s', 'tests.settings1', 'testcmd'])
    m_os_exit.assert_called_once_with(1)
