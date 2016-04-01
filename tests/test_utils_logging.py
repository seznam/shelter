
import logging

import six

from shelter.utils.logging import AddLoggerMeta


def test_add_logger_meta():

    class DummyClass(six.with_metaclass(AddLoggerMeta, object)):
        pass

    assert isinstance(DummyClass.logger, logging.Logger)
    assert DummyClass.logger.name == 'tests.test_utils_logging.DummyClass'
