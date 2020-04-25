import logging
import string
from abc import ABC, abstractmethod

from sc2 import Result, UnitTypeId

import sc2
from sc2.client import Client
from typing import TYPE_CHECKING

from sharpy.general.component import Component

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge, KnowledgeBot
    from sharpy.managers import UnitCacheManager, UnitValue


class ManagerBase(ABC, Component):
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
