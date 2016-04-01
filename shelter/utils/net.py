"""
Helpers for work with net/sockets.
"""

__all__ = ['parse_host']


def parse_host(host):
    """
    Parse *host* in format ``"[hostname:]port"`` and return :class:`tuple`
    ``(address, port)``.

        >>> parse_host('localhost:4444')
        ('localhost', 4444)
        >>> parse_host(':4444')
        ('', 4444)
        >>> parse_host('4444')
        ('', 4444)
        >>> parse_host('2001:db8::1428:57ab:4444')
        ('2001:db8::1428:57ab', 4444)
        >>> parse_host('localhost')
        ValueError: Invalid port number 'localhost'
    """
    parts = host.split(':')
    address = ':'.join(parts[:-1])
    try:
        port = int(parts[-1])
    except ValueError:
        port = None
    if not port or port < 1 or port > 65535:
        raise ValueError("Invalid port number '%s'" % port)
    return address, port
