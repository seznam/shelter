
Shelter – thin Tornado's wrapper
================================

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

::

    # Install from PyPi
    pip install shelter

    # Create new project
    shelter-admin startproject myproject

    # Start your new Tornado's application
    cd myproject/
    ./manage.py devserver

Source code
-----------

https://github.com/seznam/shelter

License
-------

3-clause BSD
