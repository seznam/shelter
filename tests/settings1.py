
NAME = 'test-shelter-app'

MANAGEMENT_COMMANDS = (
    'tests.test_main.Cmd',
)

INTERFACES = {
    'http': {
        'LISTEN': ':4443',
        'PROCESSES': 12,
        'URLS': 'tests.urls1.urls_http',
        'APP_CLASS': 'tornado.web.Application',
        'START_TIMEOUT': 30.0,
    },
    'fastrpc': {
        'LISTEN': '192.168.1.0:4445',
    },
    'rest': {
        'LISTEN': ':4447',
        'APP_CLASS': 'tests.test_core_app.ApplicationTest',
        'PROCESSES': 2,
    },
    'unix': {
        'UNIX_SOCKET': '/tmp/tornado.socket',
        'PROCESSES': 6,
        'URLS': 'tests.urls1.urls_unix',
        'APP_CLASS': 'tests.test_core_app.ApplicationTest',
    },
}
