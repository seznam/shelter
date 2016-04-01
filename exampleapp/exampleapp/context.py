
import ctypes
import multiprocessing

from shelter.core import context


class Context(context.Context):

    def __init__(self, config):
        self._value = multiprocessing.Array(ctypes.c_char, 8)
        super(Context, self).__init__(config)

    @property
    def value(self):
        return self._value.value

    @value.setter
    def value(self, v):
        self._value.value = v
