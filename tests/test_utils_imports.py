
import datetime as dt

import pytest

from shelter.utils.imports import import_object


def test_import_object():
    assert dt.timedelta == import_object('datetime.timedelta')


@pytest.mark.parametrize('name', ['', 'datetime'])
def test_import_object_fail_when_no_object(name):
    with pytest.raises(ValueError) as e:
        import_object(name)
    assert "Invalid name" in str(e)
