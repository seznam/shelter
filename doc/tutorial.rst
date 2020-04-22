
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

The first step – new project creation
-------------------------------------

For creating a project Shelter provides :option:`startproject` command. So,
create a new Python 3 isolated environment (see `virtualenv
<https://virtualenv.pypa.io/en/latest/>`_ and write in console:

.. code-block:: console

    $ shelter-admin startproject recsystem
    cd recsystem/
    python3 setup.py develop

See `The first step <https://github.com/seifert/recsystem/commit/tutorial01>`_
full diff on GitHub.

The second step – define a database schema and connection
---------------------------------------------------------

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
connection. It is :class:`!property`, so connection will be created lazily when
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

See `The second step <https://github.com/seifert/recsystem/commit/tutorial02>`_
full diff on GitHub.

The third step – fetch entities from RSS
----------------------------------------

Now we have defined the database, so we need fill the database with data. It
can be solved by script and cron job, which periodically fetches data and
stores them into database. You can write a script with this functionality,
however you must parse configuration again, create database connection and a
lot of other things. Therfore Shelter provides ancestor for writing managements
commands. The management command obtains instance of the
:class:`~shelter.core.context.Context`, so you can avoid boring things and use
all advantages which Shelter provides. For our management command we define
new configuration, object which encapsulates RSS feeder, new nethod into
storage and management command itself.

In configuration, we need URL of the RSS feed and optional timeout for network
operation. We enrich :class:`~recsystem.config.Config` by new property with
RSS feed configuration.

.. code-block:: python
    :caption: recsystem/recsystem/config.py

    import collections

    RSSFeedConfig = collections.namedtuple('RSSFeedConfig', ['url', 'timeout'])

    class Config(Config):

        @cached_property
        def rss_feed(self):
            return RSSFeedConfig(
                self._settings.RSS_FEED['url'],
                self._settings.RSS_FEED.get('timeout'),
            )

Then we enrich :class:`~recsystem.storage.Storage` by new method,
which inserts new entity into database table. The method catches
:exc:`sqlite3.IntegrityError` exception and wraps it into
:exc:`recsystem.storage.DuplicateEntry` exception. Management command
catches this exception to prevent duplicate enries.

.. code-block:: python
    :caption: recsystem/recsystem/storage.py

    class Storage(object):

        class DuplicateEntry(Exception):
            pass

        def insert_entity(self, published, guid, url, title):
            with self.connection:
                try:
                    self.connection.execute(
                        "INSERT INTO entities (published, guid, url, title) "
                        "VALUES (?, ?, ?, ?)", (published, guid, url, title))
                except sqlite3.IntegrityError:
                    raise self.DuplicateEntry(guid)

Now we have to implement fetching and parsing the RSS feed. It is easy, both
can provide awesome `feedparser <https://github.com/kurtmckee/feedparser>`_
module. Do not forget put new dependency into :file:`setup.py`.

.. code-block:: python
    :caption: recsystem/setup.py

    install_requires=[
        'feedparser',
        ...
    ],

Now we define :class:`recsystem.rssfeeder.RssFeeder` class, which encapsulates
RSS feed. The class defines :meth:`recsystem.rssfeeder.RssFeeder.iter_entries`
method. The method returns a generator, which yields an instance of the
:class:`recsystem.rssfeeder.Entry` – container which encapsulates RSS entry
attributes.

.. code-block:: python
    :caption: recsystem/recsystem/rssfeeder.py (shortened)

    import collections
    import time

    import feedparser

    Entry = collections.namedtuple(
        'Entry', ['published', 'guid', 'url', 'title'])

    class RssFeeder(object):

    def __init__(self, rss_feed_config):
        self.rss_feed_config = rss_feed_config

        def iter_entries(self):
            ...
            rss = feedparser.parse(self.rss_feed_config.url)
            ...
            for entry in rss.entries:
                yield Entry(
                    published=int(time.mktime(entry.published_parsed)),
                    guid=entry.id, url=entry.link, title=entry.title)
            ...

RSS feeder is shared resource, similar as database connection. We put
instance of the :class:`~recsystem.rssfeeder.RssFeeder` into
:class:`~recsystem.context.Context` class, so feeder will be accessible
from management commands or HTTP handlers. It is not necessary to create
instance of the feeder lazily, because instance stores only configuration,
feed is fetched every :meth:`recsystem.rssfeeder.RssFeeder.iter_entries`
call.

.. code-block:: python
    :caption: recsystem/recsystem/context.py (shortened)

    from .rssfeeder import RssFeeder

    class Context(context.Context):

        def initialize(self):
            ...
            self.rss_feeder = RssFeeder(self.config.rss_feed)

Now it is possible to write management command itself. Command defines
:attr:`~recsystem.commands.FetchRss.name` and
:attr:`~recsystem.commands.FetchRss.help`. They will be shown in console
when :option:`!--help` is passed. :meth:`~recsystem.commands.FetchRss.command`
method is an entry point for command.

.. code-block:: python
    :caption: recsystem/recsystem/commands.py (shortened)

    from shelter.core.commands import BaseCommand

    class FetchRss(BaseCommand):

        name = "fetch_rss"
        help = "fetch new entries from rss feed"

        def command(self):
            for entry in self.context.rss_feeder.iter_entries():
                try:
                    self.context.storage.insert_entity(
                        entry.published, entry.guid, entry.url, entry.title)
                except self.context.storage.DuplicateEntry:
                    pass  # Fail silently if entry has been inserted

Finally it is necessary to register the management command and configure
RSS feed. Registering is done simply by adding the command class into
:data:`settings.MANAGEMENT_COMMANDS` setting. RSS feed settings needs only
one option, url of the feed. Optionally you can specify timeout for network
operations.

.. code-block:: python
    :caption: recsystem/recsystem/settings.py

    MANAGEMENT_COMMANDS = (
        'recsystem.commands.FetchRss',
    )

    RSS_FEED = {
        'url': 'http://feeds.bbci.co.uk/news/world/rss.xml',
    }

Now :option:`fetch_rss` command is available for :command:`manage.py` command.
See help message and then try fetching enries from RSS. If you seee message
like a *Fetched 16 entities*, it works. Run periodically this command, for
example by :command:`cron`.

.. code-block:: console

    $ manage-recsystem -h
    usage: manage-recsystem [-s SETTINGS] [-h] {...,fetch_rss} ...

    positional arguments:
      {devserver,runserver,shell,showconfig,startproject,fetch_rss}
                        specify action
    ...
    fetch_rss           fetch new entries from rss feed
    ...

    $ manage-recsystem fetch_rss
    2020-04-17 22:41:43 shelter.core.commands.FetchRss INFO Fetch RSS
    2020-04-17 22:41:43 shelter.core.commands.FetchRss INFO Fetched 16 entities

See `The third step <https://github.com/seifert/recsystem/commit/tutorial03>`_
full diff on GitHub.
