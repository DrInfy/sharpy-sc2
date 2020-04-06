import logging
import string
from abc import ABC, abstractmethod

from sc2 import Result, UnitTypeId

import sc2
from sc2.client import Client


class ManagerBase(ABC):
    def __init__(self):
        self.knowledge: 'Knowledge' = None
        self.ai: sc2.BotAI = None
        self.unit_values: 'UnitValue' = None
        self._debug: bool = False

        self.client: Client = None
        self.cache: 'UnitCacheManager' = None

    @property
    def debug(self):
        return self._debug and self.knowledge.debug

    async def start(self, knowledge: 'Knowledge'):
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
