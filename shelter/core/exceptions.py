"""
Shelter's exceptions.
"""


class ShelterError(Exception):
    """
    Base error, ancestor for all other Shelter's errors.
    """

    pass


class ImproperlyConfiguredError(ShelterError):
    """
    Configuration error.
    """

    pass


class ProcessError(ShelterError):
    """
    Worker/service process error.
    """

    pass


class CommandError(ShelterError):
    """
    Management command error.
    """

    pass
