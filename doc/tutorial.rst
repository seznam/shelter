
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

Second step – define a database schema
--------------------------------------

In our example project a `SQLite <https://www.sqlite.org>`_ database is
used because it is part of Python Standard Library. So no other packages
or libraries are required. We need store entities from RSS feed and user
interactions. For simplification, only one table is defined:

First, we define a :class:`Storage` class. The class encapsulates all database
operations, because we don't want write any raw SQL in other pieces of code.
Constructor obtains database configuration and creates a connection and stores
the connection on instance. A :meth:`Storage.create_schema` method creates
database schema. The method is :func:`staticmethod`, because of prevent forking
the database connection. Shortened content of :file:`storage.py`:

.. code-block:: python

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

TODO

See `Second step <https://github.com/seifert/recsystem/commit/691d950>`_
full diff on GitHub.
