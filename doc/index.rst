
Shelter – thin Python's Tornado wrapper
=======================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

**Shelter** is a `Python's Tornado <https://www.tornadoweb.org/en/stable/>`_
wrapper which provides classes and helpers for creation new application
skeleton, writing management commands (like Django), service processes and
request handlers. It was tested with Python 2.7 and Python 3.4 or higher
and Tornado 3.2 or higher.

Instalation and quick start
---------------------------

.. code-block:: sh

    # Instalation from sources
    python setup.py install

    # Or instalation from PyPi
    pip install shelter

    # Create new project
    shelter-admin startproject myproject

    # Start your new Tornado's application
    cd myproject/
    ./manage.py devserver

shelter-admin executable
------------------------

After instalation **shelter-admin** command is available. For help type
``shelter-admin -h``:

.. code-block:: text

    usage: shelter-admin [-s SETTINGS] [-h]
                         {devserver,runserver,shell,showconfig,startproject} ...

    positional arguments:
      {devserver,runserver,shell,showconfig,startproject}
                            specify action
        devserver           run server for local development
        runserver           run server
        shell               runs a python interactive interpreter
        showconfig          show effective configuration
        startproject        generate new application skeleton

    optional arguments:
      -s SETTINGS, --settings SETTINGS
                            application settings module
      -h, --help            show this help message and exit

The most important argument is ``-s/--settings``, which joins Shelter library
and your application. Format is Python's module path, eg. ``myapp.settings``.
Second option how to handle *settings* module is ``SHELTER_SETTINGS_MODULE``
environment variable. If both are handled, command line argument has higher
priority than environment variable.

.. code-block:: sh

    shelter-admin -s myapp.settings -h

or

.. code-block:: sh

    SHELTER_SETTINGS_MODULE="myapp.settings" shelter-admin -h

Source code
-----------

https://github.com/seznam/shelter

License
-------

3-clause BSD
