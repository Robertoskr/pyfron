"""
Base pyfron backend, intended for being used as parent class for new pyfron backends
"""
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING: 
    from Pyfron.base import Pyfron


class PyfronBackend(ABC): 
    def __init__(self, pyfron: "Pyfron", *args, **kwargs): 
        self.pyfron = pyfron

    @abstractmethod
    def start(self, *args, **kwargs): 
        """
        Start the backend server, and forwards events to the pyfron project
        :args: 
            pyfron: Pyfron the project, to wich the events are going to be sent"""

    def handleEvent(self, path: str, event: dict, headers: Optional[dict]) -> tuple[int, str]: 
        return self.pyfron.onEvent(path, event)

