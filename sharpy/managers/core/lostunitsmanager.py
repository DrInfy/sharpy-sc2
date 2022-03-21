from typing import List, Dict, Tuple, Set

from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sharpy.events import UnitDestroyedEvent
from sharpy.interfaces.lost_units_manager import ILostUnitsManager
from .manager_base import ManagerBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

from sharpy.managers.core.enemy_units_manager import ignored_types


class LostUnitsManager(ManagerBase, ILostUnitsManager):
    """Keeps track of lost units. Both ours and enemies."""

    def __init__(self):
        super().__init__()
        self._cancelled_tags: Set[int] = set()
        self._my_lost_units: Dict[UnitTypeId, List[Unit]] = dict()
        self._enemy_lost_units: Dict[UnitTypeId, List[Unit]] = dict()
        self.current_lost_minerals = 0
        self.current_enemy_lost_minerals = 0
        self._last_lost_minerals = 0
        self._last_enemy_lost_minerals = 0
        self._cancel_commanded_tags: Set[int] = set()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        knowledge.register_on_unit_destroyed_listener(self.on_unit_destroyed)

    async def update(self):
        self._last_lost_minerals = self.current_lost_minerals
        self._last_enemy_lost_minerals = self.current_enemy_lost_minerals

        self.current_lost_minerals = (
            self.ai.state.score.lost_minerals_technology
            + self.ai.state.score.lost_minerals_economy
            + self.ai.state.score.lost_minerals_upgrade
        )

        self.current_enemy_lost_minerals = (
            self.ai.state.score.killed_minerals_technology
            + self.ai.state.score.killed_minerals_economy
            + self.ai.state.score.killed_minerals_upgrade
        )

    async def post_update(self):
        for action in self.ai.actions:
            if action.ability == AbilityId.CANCEL_BUILDINPROGRESS:
                if action.unit.tag not in self._cancel_commanded_tags:
                    self._cancel_commanded_tags.add(action.unit.tag)

    def on_unit_destroyed(self, event: UnitDestroyedEvent):
        if not event.unit:
            # Event is not useful if we do not know the unit.
            return

        unit = event.unit
        type_id = event.unit.type_id

        if type_id in ignored_types or unit.is_hallucination:
            return

        # Find a mapping if there is one, or use the type_id as it is
        real_type = self.unit_values.real_type(type_id)
        if unit.is_structure and unit.build_progress < 1:
            if self.cancelled(unit) and unit.tag not in self._cancelled_tags:
                self._cancelled_tags.add(unit.tag)

        if unit.is_mine:
            self._my_lost_units.setdefault(real_type, []).append(unit)
            self.print(f"Own unit destroyed, unit {unit}")
        elif unit.is_enemy:
            self._enemy_lost_units.setdefault(real_type, []).append(unit)
            self.print(f"Enemy unit destroyed, unit {unit}")
        else:
            self.print(f"Unknown owner {unit.owner_id} for unit {unit}")

    def calculate_own_lost_resources(self) -> Tuple[int, int]:
        """Calculates lost resources for our own bot. Returns a tuple with (unit_count, minerals, gas)."""
        return self._calculate_lost_resources(self._my_lost_units)

    def calculate_enemy_lost_resources(self) -> Tuple[int, int]:
        """Calculates lost resources for an enemy. Returns a tuple with (unit_count, minerals, gas)."""
        return self._calculate_lost_resources(self._enemy_lost_units)

    def own_lost_type(self, unit_type: UnitTypeId, real_type=True) -> int:
        if real_type:
            unit_type = self.unit_values.real_type(unit_type)
        return len(self._my_lost_units.get(unit_type, []))

    def enemy_lost_type(self, unit_type: UnitTypeId, real_type=True) -> int:
        if real_type:
            unit_type = self.unit_values.real_type(unit_type)
        return len(self._enemy_lost_units.get(unit_type, []))

    def _calculate_lost_resources(self, lost_units: Dict[UnitTypeId, List[Unit]]) -> tuple:
        lost_minerals = 0
        lost_gas = 0

        for unit_type in lost_units:
            count = 0
            for unit in lost_units.get(unit_type, []):
                if unit.tag in self._cancelled_tags:
                    count += 0.25
                else:
                    count += 1

            minerals = self.unit_values.minerals(unit_type) * count
            gas = self.unit_values.gas(unit_type) * count

            lost_minerals += minerals
            lost_gas += gas

        return lost_minerals, lost_gas

    async def on_end(self, game_result: Result):
        self.print_contents()

    def print_contents(self):
        lost_value = (
            self.current_lost_minerals + self.ai.state.score.lost_minerals_army + self.ai.state.score.lost_minerals_none
        )
        killed_value = (
            self.current_enemy_lost_minerals
            + self.ai.state.score.killed_minerals_army
            + self.ai.state.score.killed_minerals_none
        )
        self.print_end(f"My lost units minerals and gas: {self.calculate_own_lost_resources()}")
        self.print_end(f"My lost units minerals by score: {lost_value}")

        self.print_end(f"Enemy lost units minerals and gas: {self.calculate_enemy_lost_resources()}")
        self.print_end(f"Enemy lost units minerals by score: {killed_value}")

    def print_end(self, msg: str):
        self.knowledge.print(msg, "LostUnitsContents", stats=False)

    def get_own_enemy_lost_units(self) -> Tuple[Dict[UnitTypeId, List[Unit]], Dict[UnitTypeId, List[Unit]]]:
        """Get tuple with own and enemy lost units"""
        return (self._my_lost_units, self._enemy_lost_units)

    def cancelled(self, unit: Unit) -> bool:
        if unit.is_mine:
            if (
                unit.tag in self._cancel_commanded_tags
                and self.unit_values.minerals(unit.type_id) > self.current_lost_minerals - self._last_lost_minerals
            ):
                self.print(f"Cancel registered for {unit.type_id} {unit.tag}")
                return True
            return False  # Cancel probably didn't succeed
        if unit.is_enemy:
            if (
                unit.tag in self._cancel_commanded_tags
                and self.unit_values.minerals(unit.type_id)
                > self.current_enemy_lost_minerals - self._last_enemy_lost_minerals
            ):
                self.print(f"Cancel registered for {unit.type_id} {unit.tag}")
                return True
            return False  # Cancel probably didn't succeed

        return False
