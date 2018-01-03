
NAME = 'test-shelter-app'

MANAGEMENT_COMMANDS = (
    'tests.test_main.Cmd',
)

INTERFACES = {
    'http_both_tcp_and_unix': {
        'LISTEN': ':4443',
        'UNIX_SOCKET': '/tmp/tornado.socket',
        'PROCESSES': 12,
        'URLS': 'tests.urls1.urls_http',
    },
}
