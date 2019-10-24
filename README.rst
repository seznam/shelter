Shelter
=======

Shelter is a *Python's Tornado* wrapper which provides classes and helpers
for creation new application skeleton, writing management commands (like a
*Django*), service processes and request handlers. It was tested with
*Python 2.7* and *Python 3.4* or higher and *Tornado 3.2* or higher.

Instalation
-----------

::

    cd shelter/
    python setup.py install

After instalation **shelter-admin** command is available. For help type:

::

    shelter-admin -h

The most important argument is ``-s/--settings``, which joins Shelter library
and your application. Format is Python's module path, eg. `myapp.settings`.
Second option how to handle `settings` module is ``SHELTER_SETTINGS_MODULE``
environment variable. If both are handled, command line argument has higher
priority than environment variable.

::

    shelter-admin -s myapp.settings

or

::

    SHELTER_SETTINGS_MODULE=myapp.settings shelter-admin

Usage
------

::

    shelter-admin startproject myproject

Skeleton of the new application will be created in current working directory.
Project name has the same rules as Python's module name. Entry point into new
application is a script **manage.py**.

::

    cd myproject/
    ./manage.py -h
    ./manage.py devserver

`settings.py` is included in the new skeleton. See comments in file how to
define interfaces, management commands, service processes, ...

List of the management commands which provides Shelter library:

+ **runserver** runs production HTTP, multi-process server. Number of the
  processes are detected according to ``INTERFACES`` setting in the
  ``settings`` module. Service processes are run in separated processes.
  Parent process checks child processes and when child process exits (due to
  crash or signal), it is run again. Crashes are counted, maximum amount of
  the crashes are 100, after it whole application will be exited. If child
  stops with exit code 0, crash counter is not incremented, so you can exit
  the worker deliberately and it will be run again.
+ **devserver** runs development HTTP server, which autoreloads application
  when source files are changes. Server is run only in one process.
+ **shell** runs interactive Python's shell. First it tries to run *IPython*,
  then standard *Python* shell.
+ **showconfig** shows effective configuration.
+ **startproject** will generate new apllication skeleton.

Pay attention, service processes are run only in **runserver** command!

Config class
------------

Library provides base configuration class ``shelter.core.config.Config``
which holds all configuration. Public attributes are **settings** which
is ``settings`` module of the application and **args_parser** which is
instance of the ``argparse.ArgumentParser`` from *Python's standard library*.

You can override this class in the `settings` module::

    CONFIG_CLASS = 'myapp.core.config.AppConfig'

Your own `AppConfig` class can contain additional *properties* with
application's settings, e.g. database connection arguments. Way how the value
is found is only on you - either only in **settings** or **args_parser** or
in both. You can define additional arguments of the command line.

::

    import time

    from shelter.core.config import Config, argument

    class AppConfig(Config):

        arguments = (
            argument(
                '-k', '--secret-key',
                dest='secret_key', action='store',
                type=str, default='',
                help='configuration file'
            ),
        )

        Database = collections.namedtuple('Database', ['host', 'db'])

        def initialize(self):
            # initialize() is called after instance is created. If you want
            # add some instance attributes, use this method instead of
            # override __init__().
            self._server_started_time = time.time()

        def get_config_items(self):
            # Override get_config_items() method if you want to add
            # your options into showconfig management command.
            base_items = super(AppConfig, self).get_config_items()
            app_items = (
                ('secret_key', self.secret_key),
                ('database', self.database),
            )
            return base_items + app_items

        @property
        def secret_key(self):
            # If command-line argument -k/--secret-key exists, it will
            # override settings.SECRET_KEY value.
            return self.args_parser.secret_key or self.settings.SECRET_KEY

        @property
        def database(self):
            return self.Database(
                db=self.settings.DATABASE_NAME,
                host=self.settings.DATABASE_HOST,
                passwd=getattr(self.settings, DATABASE_PASSWORD, '')
            )

Context class
-------------

In all handlers, management commands and service processes is available
instance of the ``shelter.core.context.Context`` which holds resources for
your appllication. Bundled class ``Context`` contains only one property
**config** with ``Config`` instance (see previous chapter).

You can define own class in ``settings`` module::

    CONTEXT_CLASS = 'myapp.core.context.Context'

Overrided ``Context`` can contain additional *properties*, e.g. database
connection pool.

**It is necesary to initialize shared resources (sockets, open files, ...)
lazy!** The reason is that subprocesses (Tornado HTTP workers, service
processes) have to get uninitialized ``Context``, because forked resources
can cause a lot of nights without dreams... **Also it is necessary to known
that Context is shared among coroutines!** So you are responsible for
locking shared resources (be careful, it is blocking operation) or use
another mechanism, e.g. database connection pool.

``Context`` class contains two methods, ``initialize()`` and
``initialize_child()``.

``initialize()`` is called from constructor during instance is initialized.
So it is the best place where you can initialize attributes which can be
shared among processes.

``initialize_child()`` is called when service processes or Tornado workers
are initialized. So it is the best place where you can safely initialize
shared resources like a database connection. *process_type* argument contains
type of the child – **shelter.core.constants.SERVICE_PROCESS** or
**shelter.core.constants.TORNADO_WORKER**. *kwargs* contains additional data
according to *process_type*:

+ for **SERVICE_PROCESS** contains *process* key which is instance of the
  service process.
+ for **TORNADO_WORKER** contains *process* key which is instance of the
  HTTP worker.

::

    class Context(shelter.core.context.Context):

        def initialize(self):
            self._database = None

        def initialize_child(self, process_type, **kwargs):
            # Initialize database in the subprocesses when child is created
            self._init_database(max_connections=10)

        def _init_database(self, max_connections):
            self._database = ConnectionPool(
                self.config.database.host,
                self.config.database.db,
                max_connections=max_connections,
                connect_on_init=True)

        @property
        def database(self):
            # Lazy property if you need database connection in
            # the main process (e.g. management command)
            if self._database is None:
                self._init_database(max_connections=1)
            return self._database

Hooks
-----

You can define several hooks in the ``settings`` module - when application
is launched, on **SIGUSR1** and **SIGUSR2** signals and when instance of the
Tornado application is created.

::

    APP_SETTINGS_HANDLER = 'myapp.core.app.get_app_settings'
    INIT_HANDLER = 'myapp.core.app.init_handler'
    SIGUSR1_HANDLER = 'myapp.core.app.sigusr1_handler'
    SIGUSR2_HANDLER = 'myapp.core.app.sigusr2_handler'

``INIT_HANDLER`` is allowed to contain multiple values.

::

    INIT_HANDLER = [
        'myapp.core.app.init_handler1', 'myapp.core.app.init_handler2']

Handler is common *Python's* function which takes only one argument
*context* with ``Context`` instance (see previous chapter).

::

    def init_handler(context):
        do_something(context.config)

+ **INIT_HANDLER** is called during the application starts, before workers
  or service processes are run.
+ **SIGUSR1_HANDLER** is called on **SIGUSR1** signal. When signal receives
  worker/child process, it is processed only in this process. When signal
  receives main/parent process, signal is propagated into all workers.
+ **SIGUSR2_HANDLER** is called on **SIGUSR2** signal. Signal is processed
  only in process which received signal. It is not propagated anywhere.
+ **APP_SETTINGS_HANDLER** is called on when instance of the Tornado
  application is created. Function have to return *dict*, which is passed as
  *\*\*settings* argument into ``tornado.web.Application`` constructor. Do not
  pass *debug*, *context* and *interface* keys.

Service processes
-----------------

Service process are tasks which are repeatedly launched in adjusted interval,
e.g. warms cache data before they expire. Library provides base class
``shelter.core.process.BaseProcess``. For new service process
you must inherit ``BaseProcess``, adjust ``interval`` attribute and override
``loop()`` method.

::

    from shelter.core.processes import BaseProcess

    class WarmCache(BaseProcess)

        interval = 30.0

        def initialize(self):
            self.db_conn = self.context.db.conn_pool
            self.cache = self.context.cache

        def loop(self):
            self.logger.info("Warn cached data")
            with self.db_conn.get() as db:
                self.cache.set('key', db.get_data(), timeout=60)

+ **interval** is a time in seconds. After this time ``loop()`` method is
  repeatedly called.

Service process has to be registered in the ``settings`` module.

::

    SERVICE_PROCESSES = (
        ('myapp.processes.WarmCache', True, 15.0),
    )

Each service process definition is list/tuple in format
``('path.to.ClassName', wait_unless_ready, timeout)``. If *wait_unless_ready*
is ``True``, wait maximum *timeout* seconds unless process is successfully
started, otherwise raise ``shelter.core.exceptions.ProcessError`` exception.

Management commands
-------------------

Class ``shelter.core.commands.BaseCommand`` is an ancestor for user
defined managemend commands, e.g. export/import database data. For new
management command you must inherit ``BaseCommand`` and override ``command()``
method and/or ``initialize()`` method.

::

    import sys

    from gettext import gettext as _

    from shelter.core.commands import BaseCommand, argument

    class Export(BaseCommand)

        name = 'export'
        help = 'export data from database'
        arguments = (
            argument(
                '-o', dest=output_file, type=str, default='-',
                help=_('output filename')),
        )

        def initialize(self):
            filename = self.conntext.config.args_parser.output_file
            if filename == '-':
                self.output_file = sys.stdout
            else:
                self.output_file = open(filename, 'wt')

        def command(self):
            self.logger.info("Exporting data")
            with self.context.db.get_connection_from_pool() as db:
                data = db.get_data()
            self.output_file.write(data)
            self.output_file.flush()

+ **name** is a name of the management command. This name is used from command
  line, e.g. ``./manage.py export``.
+ **help** is a short description of the management command. This help is
  printed onto console when you type ``./manage.py command -h``.
+ **arguments** are arguments of the command line parser. ``argument()``
  function has the same meaning as ``ArgumentParser.add_argument()``
  from *Python's standard library*.
+ **settings_required** If it is ``False``, `settings` module will not be
  required for command. However, only internal ``shelter.core.config.Config``
  and ``shelter.core.context.Context`` will be available, not your own defined
  in settings. For example, internal **startprocest** command sets this flag
  to ``False``. **It is not public API, do not use this attribute unless you
  really know what you are doing**!

Management command has to be registered in the ``settings`` module.

::

    MANAGEMENT_COMMANDS = (
        'myapp.commands.Export',
    )

Interfaces
----------

*Tornado's HTTP server* can be run in multiple instances. Interface are
defined in ``settings`` module. Interfaces can be set as either TCP/IP sockets
(``LISTEN`` directive) or unix sockets (``UNIX_SOCKET`` directive) or both.

::

    INTERFACES = {
        'default': {
            # IP/hostname (not required) and port where the interface
            # listens to requests
            'LISTEN': ':8000',

            # Path to desired unix socket
            'UNIX_SOCKET': '/run/myapp.sock',

            # Amount of the server processes if application is run
            # using runserver command. Positive integer, 0 will
            # detect amount of the CPUs
            'PROCESSES': 0,

            # Path in format 'path.to.module.variable_name' where
            # urls patterns are defined
            'URLS': 'myapp.urls.default_urls',

            # Path in format 'path.to.module.variable_name' to class
            # of the Tornado's application. If not specified, default
            # tornado.web.Application is used. 
            'APP_CLASS': 'myapp.core.app.TornadoApplication',
        },
    }

URL path to HTTP handler routing
--------------------------------

It is the same as in *Python's Tornado* application.

::

    from tornado.web import URLSpec

    from myapp.handlers import HomepageHandler, AboutHandler

    urls_default = (
        URLSpec(r'/', HomepageHandler),
        URLSpec(r'/about/', AboutHandler),
    )

Tuple/list **urls_default** is handled into relevant interface in the
``settings`` module, see previous chapter.

HTTP handler is a subclass of the ``shelter.core.web.BaseRequestHandler``
which enhances ``tornado.web.RequestHandler``. Provides additional instance
attributes/properties **logger**, **context** and **interface**.

+ **logger** is an instance of the ``logging.Logger`` from *Python's standard
  library*. Logger name is derived from handlers's name, e.g
  ``myapp.handlers.HomepageHandler``.
+ **context** is an instance of the ``Context``, see *Context* paragraph.
+ **interface** is a namedtuple with informations about current interface.
  Named attributes are **name**, **host**, **port**, **processes** and
  **urls**.

::

    from shelter.core.web import BaseRequestHandler

    class DummyHandler(BaseRequestHandler):

        def get(self):
            self.write(
                "Interface '%s' works!\n" % self.interface.name)
            self.set_header(
                "Content-Type", 'text/plain; charset=UTF-8')

Logging
-------

Standard *Python's logging* is used. ``Config.configure_logging()`` method
is responsible for setting the logging. Default ``Config`` class reads
logging's configuration from ``settings`` module::

    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
            },
        },
        'root': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    }

Contrib
-------

shelter.contrib.config.iniconfig.IniConfig
``````````````````````````````````````````

Descendant of the ``shelter.core.config.Config``, provides **INI** files
configuration. Adds additional public attribute **config_parser** which is
instance of the ``RawConfigParser`` from *Python's standard library*.
Interfaces and application's name can be overrided in configuration file,
*Python's logging* must be defined.

Configuration file is specified either by ``SHELTER_CONFIG_FILENAME``
environment variable or ``-f/--config-file`` command line argument. First,
main configuration file is read. Then all configuration files from
``file.conf.d`` subdirectory are read in alphabetical order. E.g. if
``-f conf/myapp.conf`` is handled, first ``conf/myapp.conf`` file is read
and then all ``conf/myapp.conf.d/*.conf`` files. Value in later
configuration file overrides previous defined value.

::

    [application]
    name = MyApp

    [interface_http]
    Listen=:4444
    Processes=8
    Urls=tests.urls1.urls_http
    AppClass=myapp.core.app.TornadoApplication

    [formatters]
    keys=default

    [formatter_default]
    class=logging.Formatter
    format=%(asctime)s %(name)s %(levelname)s: %(message)s

    [handlers]
    keys=console

    [handler_console]
    class=logging.StreamHandler
    args=()
    level=NOTSET

    [loggers]
    keys=root

    [logger_root]
    level=INFO
    handlers=console

License
-------

3-clause BSD
