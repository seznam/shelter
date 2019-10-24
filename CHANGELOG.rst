2.2.0
-----

+ Added ``APP_CLASS`` option into ``settings.INTERFACES``.

2.1.2
-----

+ Fixed stopping processes in runserver command.

2.1.1
-----

+ Fixed main process exiting.

2.1.0
-----

+ Added ``app_settings_handler`` hook.

2.0.0
-----

+ Semantic versioning
+ ``settings.INIT_HANDLER`` can be either string or list of strings
+ Service processes are started only in `runserver` command
+ ``Config.command_name`` contains name of the current management command
+ Clean code, fixes
+ Sphinx documentation

Upgrade from 1.1.x
``````````````````

+ Constants ``shelter.core.processes.SERVICE_PROCESS`` and
  ``shelter.core.processes.TORNADO_WORKER`` are moved to
  ``shelter.core.constants``.
+ ``Context.initialize_child`` keywords arguments are changed.
+ Majority of ``shelter.core.commands.BaseCommand`` control attributes are
  removed, only ``settings_required`` is now available.
+ ``context`` and ``interface`` are not passed as keywords arguments into
  ``shelter.core.web.BaseRequestHandler`` constructor.

1.1.5
-----

+ Fixed exiting of the main process when children exist and error is occurred
+ PEP 396 module version info

Upgrade from 1.1.4
``````````````````

``version_info`` attribute is removed from ``shelter`` module, ``version``
attribute is replaced by ``__version__``.

1.1.4
-----

+ Fixed constructing list of the sockets in devserver command

1.1.3
-----

+ Add ``initialize_child()`` method into ``shelter.core.context.Context``
+ Always restart worker when it stops
+ Interfaces now support UNIX sockets for communication

1.1.2
-----

+ *devserver* and *shell* management commands now start service processes
  in threads.
+ Add ``initialize()`` method into ``shelter.core.processes.BaseProcess``
  class.
+ Some minor improvements.

1.1.1
-----

+ Fixed ``shelter.contrib.config.iniconfig.IniConfig`` class
+ Fixed documentation

1.1.0
-----

+ **INI** files support was removed from base ``shelter.core.config.Config``
+ Added new ``shelter.contrib.config.iniconfig.IniConfig`` class which
  provides **INI** files configuration.
+ ``settings.LOGGING_FROM_CONFIG_FILE`` is no longer supported.
+ Added ``initialize()`` method into ``shelter.core.config.Config`` and
  ``shelter.core.context.Context`` classes.

Upgrade from 1.0.0
``````````````````

+ Remove ``LOGGING_FROM_CONFIG_FILE`` from ``settings`` module.
+ If you use **INI** file configuration, change ancestor of your ``Config`` from
  ``shelter.core.config.Config`` to ``shelter.contrib.config.iniconfig.IniConfig``
  and set *Python's logging* in configuration file.

1.0.0
-----

* First release
