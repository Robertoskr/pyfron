from pyfron.backends import PyfronBackend
import ctypes
from ctypes import POINTER, 


class GolangBackend(PyfronBackend): 
    def start(self, *args, **kwargs): 
        library = ctypes.cdll.LoadLibrary(
                "./pyfron/backends/GolangBackend/library.so"
        )
        library.startPyFronServer()

