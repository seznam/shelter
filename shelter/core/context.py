"""
Module :module:`shelter.core.context` provides base class which
encapsulates data for HTTP handlers.
"""

__all__ = ['Context']


class Context(object):
    """
    Class which encapsulates data (configuration, database connection,
    other resources...) for HTTP handlers.

    .. warning::

       Instance is created before running the server. Do not create
       instance of the shared resources (sockets, files, ...) in
       constructor, it is necessary initialize them lazy!
    """

    def __init__(self, config):
        self._config = config

    @classmethod
    def from_config(cls, config):
        """
        According to application's configuration *config* create and
        return new instance of the **Context**.
        """
        return cls(config)

    @property
    def config(self):
        """
        Application's configuration.
        """
        return self._config
