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
