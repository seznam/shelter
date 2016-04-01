
import pytest

from shelter.utils.net import parse_host


@pytest.mark.parametrize(
    'host,expected',
    [
        ('4444', ('', 4444)),
        (':4444', ('', 4444)),
        ('127.0.0.1:4444', ('127.0.0.1', 4444)),
        ('localhost:4444', ('localhost', 4444)),
        ('localhost.localdomain:4444', ('localhost.localdomain', 4444)),
        (
            '2001:0db8:0000:0000:0000:0000:1428:57ab:4444',
            ('2001:0db8:0000:0000:0000:0000:1428:57ab', 4444)
        ),
        ('2001:db8::1428:57ab:4444', ('2001:db8::1428:57ab', 4444)),
        ('::1:4444', ('::1', 4444)),
    ]
)
def test_parse_host(host, expected):
    assert parse_host(host) == expected


@pytest.mark.parametrize(
    'host',
    [
        'localhost:port',
        'localhost:-1',
        'localhost:0',
        'localhost:65536'
    ]
)
def test_parse_host_fail_when_invalid_port_number(host):
    with pytest.raises(ValueError) as e:
        parse_host(host)
    assert "Invalid port number" in str(e)
