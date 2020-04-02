
Developers guide
================

.. py:module:: settings

``settings`` – basic configuration of your application
------------------------------------------------------

Basic configuration of your application is placed in :mod:`!settings`
module. It is common Python module, which is passed into Shelter using
either :option:`-s/--settings` command line argument or
:envvar:`SHELTER_SETTINGS_MODULE` environment variable. It contains a few
options for basic application settings. :option:`startproject` management
command creates two entry points, :command:`applicationname/manage.py`
script and :command:`manage-applicationname` executable. Both have
pre-configured settings module to :mod:`!applicationname.settings`, so you
needn't explicitly specify :mod:`!settings` module if you use these entry
points.

.. code-block:: sh

    # Pass settings module using -s argument
    shelter-admin -s myapplicaton.settings command

    # Pass settings module using environment variable
    SHELTER_SETTINGS_MODULE=myapplicaton.settings shelter-admin command

    # Use manage.py script
    cd myapplicaton
    ./manage.py command

    # Use manage-applicationname entry point
    manage-myapplicaton command

List of basic settings
^^^^^^^^^^^^^^^^^^^^^^

NAME
""""

Default: name of the executable

Name of the application. This name will be shown in the OS process list.

.. code-block:: python

    NAME = 'MyApplicaton'

INIT_HANDLER
""""""""""""

Default: ``None``

Hook, which is called when application is initialized. It is called from
main process when application is launched. Target function receives only
one argument, instance of the :class:`~shelter.core.context.Context`,
returns nothing.

.. code-block:: python

    INIT_HANDLER = 'myapplicaton.hooks.init_handler'

APP_SETTINGS_HANDLER
""""""""""""""""""""

Default: ``None``

Hook, which is called when instance of the :class:`~tornado.web.Application`
is created. Target function receives only one argument, instance of the
:class:`~shelter.core.context.Context` and returns :class:`!dict` with
additional arguments, which are passed into :class:`~!tornado.web.Application`
constructor as a keywords arguments (note that there is *settings* argument
in :class:`~!tornado.web.Application` constructor, but it is not Shelter
:mod:`settings`, it is only same name).

.. code-block:: python

    APP_SETTINGS_HANDLER = 'myapplicaton.hooks.app_settings_handler'

SIGUSR1_HANDLER
"""""""""""""""

Default: ``None``

Hook, which is called when when ``SIGUSR1`` signal is received. Target
function receives only one argument, instance of the
:class:`~shelter.core.context.Context`, returns nothing. Function is
called in the main process and in all workers and service processes.

.. code-block:: python

    SIGUSR1_HANDLER = 'myapplicaton.hooks.sigusr1_handler'

SIGUSR2_HANDLER
"""""""""""""""

Default: ``None``

Hook, which is called when when ``SIGUSR2`` signal is received. Target
function receives only one argument, instance of the
:class:`~shelter.core.context.Context`, returns nothing. Function is
called only in process which received signal.

.. code-block:: python

    SIGUSR2_HANDLER = 'myapplicaton.hooks.sigusr2_handler'

CONFIG_CLASS
""""""""""""

Default: ``'shelter.core.config.Config'``

Application configuration class. Shelter provides default
:class:`~shelter.core.config.Config` class, which converts basic options
from :mod:`settings` module to instance attributes.

.. code-block:: python

    CONFIG_CLASS = 'myapplicaton.config.Config'

CONTEXT_CLASS
"""""""""""""

Default: ``'shelter.core.context.Context'``

Application context class. Context is a container for shared
resources, e.g. database connection. Shelter provides default
:class:`~shelter.core.context.Context` class.

.. code-block:: python

    CONTEXT_CLASS = 'myapplicaton.context.Context'

MANAGEMENT_COMMANDS
"""""""""""""""""""

Default: ``()`` (empty :class:`!tuple`)

List of management commands. Management command is one-time task,
:class:`~shelter.core.commands.BaseCommand` descendant. It is launched
from command line, obtains instance of the
:class:`~shelter.core.context.Context` of your application and can do
anything, e.g. dump database data. If you type ``./manage --help`` in
console, commands are printed in help messages.

.. code-block:: python

    MANAGEMENT_COMMANDS = (
        'myapplicaton.commands.DumpDatabase',
    )

SERVICE_PROCESSES
"""""""""""""""""

Default: ``()`` (empty :class:`!tuple`)

List of service processes definition. Service process is tasks, which is
launched in separated process and it is are periodically called in adjusted
interval. It is :class:`~shelter.core.processes.BaseProcess` descendant.
It is started only if :option:`runserver` command is run, obtains instance
of the :class:`~shelter.core.context.Context` of your application and can
do anything while server is alive, e.g. periodically pre-caches data from
database into memory. Each item is a tuple
``('path.to.Class', wait_unless_ready, timeout)``. *path.to.Class* is service
process class. *wait_unless_ready* is :class:`!bool`, if :data:`!True`, main
process will wait maximum *timeout* seconds until process is successfully
started. If :data:`!False`, set *timeout* to :data:`!0` or :data:`!None`.

.. code-block:: python

    SERVICE_PROCESSES = (
        ('myapplicaton.processes.PreloadData', True, 5.0),
    )

INTERFACES
""""""""""

Default: no default value, required option

HTTP server interfaces. Your application can listen to multiple ports and
each port can handles different urls. You can specify either :data:`LISTEN`
or :data:`UNIX_SOCKET` option, or both together.

.. code-block:: python

    INTERFACES = {
        'default': {
            # Port number to listen to.
            'LISTEN': ':8000',

            # Path to desired unix socket.
            'UNIX_SOCKET': '/run/myapp.sock',

            # Python path to tuple containing URL paths to HTTP handlers
            # routing.
            'URLS': 'myapplicaton.urls.urls_default',

            # Number of the server processes, positive number, 0 means number
            # of the CPU cores. Optional, default value is 1.
            'PROCESSES': 0,

            # Python path to custom implementaion of Tornado Application
            # class. Optional, default is 'tornado.web.Application'.
            'APP_CLASS': 'myapplicaton.apps.CustomApplicationClass',
        },
    }

``shelter.core.config`` – application configuration class
---------------------------------------------------------

.. automodule:: shelter.core.config

.. autofunction:: shelter.core.config.argument

.. autoclass:: shelter.core.config.Config

``shelter.core.context`` – container for shared resources
---------------------------------------------------------

.. automodule:: shelter.core.context

.. autoclass:: shelter.core.context.Context

``shelter.core.commands`` – one-time task
-----------------------------------------

.. automodule:: shelter.core.commands

.. autoclass:: shelter.core.commands.BaseCommand

``shelter.core.processes`` – periodically called tasks
------------------------------------------------------

.. automodule:: shelter.core.processes

.. autoclass:: shelter.core.processes.BaseProcess
