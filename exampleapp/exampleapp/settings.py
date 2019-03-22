
NAME = 'exampleapp'

# Change it!!!
SECRET_KEY = '!VstwEzRZ3Stqd5#3V$tAA#cDbedg@!rVz!xw!R5xBZS2B#bbE@DdZe#DF5s!@zv'

INIT_HANDLER = 'exampleapp.app.init_handler'

SIGUSR1_HANDLER = 'exampleapp.app.sigusr1_handler'

SIGUSR2_HANDLER = 'exampleapp.app.sigusr2_handler'

APP_SETTINGS_HANDLER = 'exampleapp.app.app_settings_handler'

CONFIG_CLASS = 'exampleapp.config.Config'

CONTEXT_CLASS = 'exampleapp.context.Context'

MANAGEMENT_COMMANDS = (
    'exampleapp.commands.HelloWorld',
)

SERVICE_PROCESSES = (
    ('exampleapp.processes.WarmCache', True, 5),
)

INTERFACES = {
    'default': {
        'LISTEN': ':8000',
        'PROCESSES': 2,
        'URLS': 'exampleapp.urls.urls_default',
    },
    'debug': {
        'LISTEN': ':8001',
        'PROCESSES': 1,
    },
}
