
NAME = 'test-shelter-app'

MANAGEMENT_COMMANDS = (
    'tests.test_main.Cmd',
)

INTERFACES = {
    'http': {
        'LISTEN': ':4443',
        'PROCESSES': 12,
        'URLS': 'tests.urls1.urls_http',
    },
    'fastrpc': {
        'LISTEN': '192.168.1.0:4445',
    },
    'unix': {
        'UNIX_SOCKET': '/tmp/tornado.socket',
        'PROCESSES': 12,
        'URLS': 'tests.urls1.urls_unix',
    },
}
