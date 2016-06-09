
import logging

import mock
import pytest

from shelter.core.commands import BaseCommand


def test_base_command():
    context = mock.Mock()
    context.config.settings.SERVICE_PROCESSES = ()
    context.config.logging = {}
    context.config.name = 'test-shelter-app'
    context.config.init_handler = None
    context.config.sigusr1_handler = None
    context.config.sigusr2_handler = None
    context.config.logging_from_config_file = False
    config = mock.Mock()
    config.context_class.from_config.return_value = context

    cmd = BaseCommand(config)
    with pytest.raises(NotImplementedError):
        cmd()

    assert cmd.context == context
    assert isinstance(cmd.logger, logging.Logger)
    assert cmd.logger.name == 'shelter.core.commands.BaseCommand'
