
Shelter
=======

Introduction
------------

Goal
""""

Shelter is a `Python Tornado <https://www.tornadoweb.org/en/stable/>`_
wrapper. It provides with classes and helpers for creation of a new
application skeleton, writing management commands, service processes
and request handlers.

When you write a new application a lot of things are the same and boring.
You have to write a configuration parser, a Tornado application class, or a
runner. See `Hello World <https://www.tornadoweb.org/en/stable/#hello-world>`_
example. Shelter tries solving such boring things as these are.

Why the name Shelter? Tornado is an element, so Shelter tries to save
you against the element :-).

Main features
"""""""""""""

- Ancestor for class which holds configuration.
- Ancestor for container for shared resources, e.g. database connection.
  Instance of this class is accessible in all HTTP handlers and hooks.
- Hooks – functions, which are called upon when some events appeare, e.g.
  when the server is launched or some signals are received.
- Service processes – tasks, which are launched in separated process and
  which are periodically called upon in an adjusted interval.
- Management commands – one-time tasks, which are launched from the command
  line. Several commands are included in the library, e.g. :option:`devserver`
  for running HTTP server in a development mode or :option:`runserver` for
  production.
- Multiple ports, where HTTP server listens to requets and there are a
  multiple related Tornado applications for them.
- Only one entry point for url → HTTP handler routing.
- Both Python 2.7 and Python 3.4 or higher are supported.

Instalation and quick start
---------------------------

Installation from source code:

.. code-block:: console

    $ git clone https://github.com/seznam/shelter.git
    $ cd shelter
    $ python setup.py install

Installation from PyPi:

.. code-block:: console

    $ pip install shelter

After installation :command:`shelter-admin` command is available. For help
type ``shelter-admin -h``:

.. code-block:: console

    $ shelter-admin -h
    usage: shelter-admin [-s SETTINGS] [-h]
                         {devserver,runserver,shell,showconfig,startproject} …

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

The most important argument is :option:`-s/--settings`. It connets
Shelter library and your application. The format is Python module path, eg.
``myproject.settings``. The second option how to pass settings module is
:envvar:`SHELTER_SETTINGS_MODULE` environment variable. If both are passed,
the command line argument has a higher priority than environment variable.

.. code-block:: console

    $ # Pass settings module using -s argument
    $ shelter-admin -s myapp.settings command

    $ # Pass settings module using environment variable
    $ SHELTER_SETTINGS_MODULE=myapp.settings shelter-admin command

For creating a new project skeleton, Shelter provides :option:`startproject`
command. The project name has the same rules as Python module name. The entry
point into new application is a script :command:`manage.py`. The command
:option:`devserver` runs the project (HTTP server, which listens to e requests
on a default port ``:8000``) in the development mode.

.. code-block:: console

    $ shelter-admin startproject myproject
    $ cd myproject/
    $ ./manage.py devserver

Type ``http://localhost:8000/`` into your browser. If you see text
"**myproject - example handler**", it works!

Tutorial
--------

.. toctree::
   :maxdepth: 3

   tutorial

Reference manual
----------------

.. toctree::
   :maxdepth: 2

   reference-manual

Source code and license
-----------------------

Source codes are available on GitHub `https://github.com/seznam/shelter
<https://github.com/seznam/shelter>`_ under the `3-clause BSD license
<https://opensource.org/licenses/BSD-3-Clause>`_.
