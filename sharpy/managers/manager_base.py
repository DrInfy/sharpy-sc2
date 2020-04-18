import logging
import string
from abc import ABC, abstractmethod

from sc2 import Result, UnitTypeId

import sc2
from sc2.client import Client
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge, KnowledgeBot
    from sharpy.managers import UnitCacheManager, UnitValue


class ManagerBase(ABC):
    ai: "KnowledgeBot"
    knowledge: "Knowledge"
    unit_values: "UnitValue"
    cache: "UnitCacheManager"
    client: Client

    def __init__(self):
        self._debug: bool = False

    @property
    def debug(self):
        return self._debug and self.knowledge.debug

    async def start(self, knowledge: "Knowledge"):
        self.knowledge = knowledge
        self._debug = self.knowledge.config["debug"].getboolean(type(self).__name__)
        self.ai = knowledge.ai
        self.client = self.ai._client
        self.cache = knowledge.unit_cache
        self.unit_values = knowledge.unit_values

    @abstractmethod
    async def update(self):
        pass

    def real_type(self, type_id: UnitTypeId) -> UnitTypeId:
        return self.unit_values.real_type(type_id)

    @abstractmethod
    async def post_update(self):
        pass

    def print(self, msg: string, stats: bool = True, log_level=logging.INFO):
        self.knowledge.print(msg, type(self).__name__, stats, log_level)

    async def on_end(self, game_result: Result):
        pass
