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
        self.initialize()

    @classmethod
    def from_config(cls, config):
        """
        According to application's configuration *config* create and
        return new instance of the **Context**.
        """
        return cls(config)

    def initialize(self):
        """
        Initialize instance attributes. This method is called when instance
        is initialized. You can override this method in the subclasses.
        """
        pass

    def initialize_child(self, process_type, **kwargs):
        """
        Initialize instance attributes, it is similar to :meth:`initialize`.
        However, method is called only in the children (workers of the
        Tornado, service processes) when child is initialized and before
        HTTP server is started. *process_type* indicates type of the process,
        it can be :data:`shelter.core.constants.SERVICE_PROCESS` or
        :data:`shelter.core.constants.TORNADO_WORKER`. *kwargs* contains
        additional data according to *process_type*. You can override this
        method in the subclasses.
        """
        pass

    @property
    def config(self):
        """
        Application's configuration.
        """
        return self._config
