import logging
import sys
import threading
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Optional, List

from sc2.units import Units
from sharpy.knowledges.skeleton_bot import SkeletonBot
from sharpy.combat.group_combat_manager import GroupCombatManager
from sharpy.managers.core import *
from sharpy.managers.extensions import *
from config import get_config, get_version
from sc2.unit import Unit
import time

if TYPE_CHECKING:
    from sharpy.knowledges import BuildOrder


class KnowledgeBot(SkeletonBot, ABC):
    """Base class for bots that are built around Knowledge class."""

    def __init__(self, name: str):
        super().__init__(name)
        self.memory_manager = MemoryManager()
        self.lost_units_manager = LostUnitsManager()
        self.enemy_units_manager = EnemyUnitsManager()
        self.unit_cache = UnitCacheManager()
        self.unit_value = UnitValue()
        self.roles = UnitRoleManager()
        self.pathing_manager = PathingManager()
        self.zone_manager = ZoneManager()
        self.building_solver = BuildingSolver()
        self.income_calculator = IncomeCalculator()
        self.cooldown_manager = CooldownManager()
        self.combat = GroupCombatManager()
        self.heatmap_manager = HeatMapManager()
        self.gather_point_solver = GatherPointSolver()
        self.previous_units_manager = PreviousUnitsManager()
        self.game_analyzer = GameAnalyzer()
        self.data_manager = DataManager()

    async def on_start(self):
        """Allows initializing the bot when the game data is available."""
        user_managers = self.configure_managers()

        managers = [
            self.memory_manager,
            self.lost_units_manager,
            self.enemy_units_manager,
            self.unit_cache,
            self.unit_value,
            self.roles,
            self.pathing_manager,
            self.zone_manager,
            self.building_solver,
            self.income_calculator,
            self.cooldown_manager,
            self.combat,
            self.heatmap_manager,
            self.gather_point_solver,
            self.previous_units_manager,
            self.game_analyzer,
            self.data_manager,
        ]
        if user_managers:
            managers.extend(user_managers)
        managers.append(CustomFuncManager(self.pre_step_execute))
        managers.append(ActManager(self.create_plan))
        self.knowledge.pre_start(self, managers)
        await self.knowledge.start()
        self._log_start()

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        return []

    @abstractmethod
    async def create_plan(self) -> "BuildOrder":
        pass

    async def pre_step_execute(self):
        pass

    def _log_start(self):
        def log(message):
            self.knowledge.print(message, tag="Start", stats=False)

        log(f"My race: {self.knowledge.my_race.name}")
        log(f"Opponent race: {self.knowledge.enemy_race.name}")
        log(f"OpponentId: {self.opponent_id}")
