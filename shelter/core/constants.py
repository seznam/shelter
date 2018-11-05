"""
Module :module:`shelter.core.constants` contains useful constants used
in Shelter.
"""

__all__ = ['SERVICE_PROCESS', 'TORNADO_WORKER']

SERVICE_PROCESS = 'service_process'
"""
Indicates that type of the process is a service process. *kwargs* argument
in method :meth:`shelter.core.context.initialize_child` contains *process*,
which holds instance of the service process.
"""

TORNADO_WORKER = 'tornado_worker'
"""
Indicates that type of the process is a Tornado HTTP worker. *kwargs*
argument in method :meth:`shelter.core.context.initialize_child` contains
*app*, which holds Tornado's application associated with this worker and
*http_server*, which holds instance of the ``tornado.httpserver.HTTPServer``.
"""
