
from shelter.core.cmdlineparser import argument


def test_argument_empty():
    assert argument() == ((), {})


def test_argument_args():
    assert argument('-h', '--help') == (('-h', '--help'), {})


def test_argument_kwargs():
    expected = ((), {'dest': 'help', 'type': str})
    assert argument(dest='help', type=str) == expected


def test_argument_both():
    expected = (('-h', '--help'), {'dest': 'help', 'type': str})
    assert argument('-h', '--help', dest='help', type=str) == expected
