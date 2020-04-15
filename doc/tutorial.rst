
Tutorial
========

Preamble
--------

This tutorial will explain how to write a new project. Let's go write simple
recommendation system. We have some website with articles. Website provides a
RSS feed with articles. We want to sort articles according to their popularity.
So, our recommendation system will have to parse and collect articles from the
RSS feed, collect user interactions and finally provides recommendation.

Terminology
^^^^^^^^^^^

================ =============================================================
Name             Description
================ =============================================================
entity           one item from RSS feed
user interaction information if user clics on entity or does not
alpha            information than user clicked on some advertised entity,
                 type of user interaction
beta             information than user did not click on any advertised entity,
                 type of user interaction
ctr              click-through rate, ratio of users who click on the advertised
                 entity to the number of total users who view a page
================ =============================================================

First step – new project creation
---------------------------------

For creating a project Shelter provides :option:`startproject` command. So,
create a new Python 3 isolated environment (see `virtualenv
<https://virtualenv.pypa.io/en/latest/>`_ and write in console:

.. code-block:: sh

    shelter-admin startproject recsystem
    cd recsystem/
    python3 setup.py develop

See `First step <https://github.com/seifert/recsystem/commit/258eea7>`_
full diff on GitHub.

Second step – define a database schema and connection
-----------------------------------------------------

In our example project a `SQLite <https://www.sqlite.org>`_ database is
used because it is part of Python Standard Library. So no other packages
or libraries are required. Of course, for production, using different type
of database is recommended. We need store entities from RSS feed and user
interactions. For simplification, only one table is defined.

First, we define a :class:`~recsystem.storage.Storage` class. The class
encapsulates all database operations, because we do not want write any raw
SQL in other pieces of code. Constructor obtains database configuration and
creates a connection and stores the connection on instance. A
:meth:`Storage.create_schema` method creates database schema. The method
is :func:`!staticmethod`, because of prevent forking the database connection
in multiprocess environment. So create a new module :mod:`recsystem.storage`
and place :class:`~recsystem.storage.Storage` class into the module.

.. code-block:: python
    :caption: recsystem/recsystem/storage.py (shortened)

    import sqlite3

    DB_SCHEMA = """
        CREATE TABLE IF NOT EXISTS entities (
            ...
        );
    """

    class Storage(object):

        def __init__(self, **database_kwargs):
            self._connection = self.get_connection(**database_kwargs)

        @staticmethod
        def get_connection(**database_kwargs):
            return sqlite3.connect(**database_kwargs)

        @classmethod
        def create_schema(cls, **database_kwargs):
            ...

Next, is it necessary to read the database configuration, which is stored
in the :mod:`settings` module. Shelter provides
:class:`~shelter.core.config.Config` class, container for configuration. So
we enrich this class with database configuration.

.. code-block:: python
    :caption: recsystem/recsystem/config.py

    from cached_property import cached_property
    from shelter.core.config import Config

    class Config(Config):

        @cached_property
        def database(self):
            return self._settings.DATABASE

New third party package :mod:`cached-property` is used, do not forget to put
this new dependency into :file:`setup.py`.

.. code-block:: python
    :caption: recsystem/setup.py

    install_requires=[
        'cached-property',
        ...
    ],

Ok, we have :class:`~recsystem.storage.Storage` class and overrided
:class:`~recsystem.config.Config` class. Now we create the database connection.
:class:`~shelter.core.context.Context` is a container for shared resources and
the database connection is one of these resources. So we override this class
and enrich the class with database connection.
:class:`~shelter.core.context.Context` class provides
:meth:`~shelter.core.context.Context.initialize` method, which is called when
server is started and :class:`~shelter.core.context.Context` instance is
created. So if we call :meth:`recsystem.storage.Storage.create_schema` in
:meth:`~shelter.core.context.Context.initialize` method, the database schema
will be created during starting the server.
:attr:`recsystem.context.Context.database` attribute holds the database
connection. It is :class:`!property`, so connection will be created lazy when
it is accessed first time. Reason is prevent forking the connection in
multiprocess environment.

.. code-block:: python
    :caption: recsystem/recsystem/context.py

    from cached_property import cached_property
    from shelter.core import context

    from .storage import Storage

    class Context(context.Context):

        def initialize(self):
            Storage.create_schema(**self.config.database)

        @cached_property
        def storage(self):
            return Storage(**self.config.database)

Finally we have to register our overrided :class:`~recsystem.config.Config` and
:class:`~recsystem.context.Context` in the :mod:`settings` module and put the
database configuration option. The database configuration is a :class:`!dict`
and it will be passed as a *\*\*kwargs* argument into database connect
function. In our example, database file path is constructed dynamically and the
file is placen into temporary directory, so server is able to be run without
any manual intervention. In production environment using real path is
necessary.

.. code-block:: python
    :caption: recsystem/recsystem/settings.py

    import os.path
    import tempfile

    CONFIG_CLASS = 'recsystem.config.Config'

    CONTEXT_CLASS = 'recsystem.context.Context'

    DATABASE = {
        'database': os.path.join(tempfile.gettempdir(), 'recsystem.db'),
    }

See `Second step <https://github.com/seifert/recsystem/commit/d4efe24>`_
full diff on GitHub.
