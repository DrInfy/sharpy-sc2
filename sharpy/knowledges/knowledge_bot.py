import logging
import sys
import threading
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from sc2.units import Units
from sharpy.knowledges.skeleton_bot import SkeletonBot
from sharpy.combat.group_combat_manager import GroupCombatManager
from sharpy.managers.core import *
from sharpy.managers.extensions import *
from config import get_config, get_version
from sc2 import BotAI, Result, Optional, UnitTypeId, List
from sc2.unit import Unit
import time

if TYPE_CHECKING:
    from sharpy.knowledges import BuildOrder


class KnowledgeBot(SkeletonBot, ABC):
    """Base class for bots that are built around Knowledge class."""

    async def on_start(self):
        """Allows initializing the bot when the game data is available."""
        managers = [
            MemoryManager(),
            LostUnitsManager(),
            EnemyUnitsManager(),
            UnitCacheManager(),
            UnitValue(),
            UnitRoleManager(),
            PathingManager(),
            ZoneManager(),
            BuildingSolver(),
            IncomeCalculator(),
            CooldownManager(),
            GroupCombatManager(),
            GatherPointSolver(),
            PreviousUnitsManager(),
            GameAnalyzer(),
            DataManager(),
        ]

        user_managers = self.configure_managers()
        if user_managers:
            managers.extend(user_managers)
        managers.append(CustomFuncManager(self.pre_step_execute))
        managers.append(ActManager(self.create_plan))
        self.knowledge.pre_start(self, managers)
        await self.knowledge.start()

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        return []

    @abstractmethod
    async def create_plan(self) -> "BuildOrder":
        pass

    async def pre_step_execute(self):
        pass
