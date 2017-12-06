
NAME = 'test-shelter-app'

MANAGEMENT_COMMANDS = (
    'tests.test_main.Cmd',
)

INTERFACES = {
    'http_neither_tcp_nor_unix': {
        'PROCESSES': 12,
        'URLS': 'tests.urls1.urls_http',
    },
}
