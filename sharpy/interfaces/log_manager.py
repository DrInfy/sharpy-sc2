import logging
import string
from abc import abstractmethod, ABC


class ILogManager(ABC):
    @abstractmethod
    def print(self, message: string, tag: string = None, stats: bool = True, log_level=logging.INFO):
        pass
