from typing import List, Dict, Tuple

from sharpy.events import UnitDestroyedEvent
from sharpy.managers import ManagerBase
from sc2 import UnitTypeId, Result
from sc2.unit import Unit

from sharpy.managers.enemy_units_manager import ignored_types


class LostUnitsManager(ManagerBase):
    """Keeps track of lost units. Both ours and enemies."""

    def __init__(self):
        super().__init__()
        self.hallucination_tags: List[int] = []

        self._my_lost_units: Dict[UnitTypeId, List[Unit]] = {}
        self._enemy_lost_units: Dict[UnitTypeId, List[Unit]] = {}

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        knowledge.register_on_unit_destroyed_listener(self.on_unit_destroyed)

    async def update(self):
        pass

    async def post_update(self):
        pass

    def on_unit_destroyed(self, event: UnitDestroyedEvent):
        if not event.unit:
            # Event is not useful if we do not know the unit.
            return

        unit = event.unit
        type_id = event.unit.type_id

        if type_id in ignored_types or unit.tag in self.hallucination_tags:
            return

        # Find a mapping if there is one, or use the type_id as it is
        real_type = self.unit_values.real_type(type_id)

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

    def own_lost_type(self, unit_type: UnitTypeId) -> int:
        real_type = self.unit_values.real_type(unit_type)
        return len(self._my_lost_units.get(real_type, []))

    def enemy_lost_type(self, unit_type: UnitTypeId) -> int:
        real_type = self.unit_values.real_type(unit_type)
        return len(self._enemy_lost_units.get(real_type, []))

    def _calculate_lost_resources(self, lost_units: Dict[UnitTypeId, List[Unit]]) -> tuple:
        lost_minerals = 0
        lost_gas = 0

        for unit_type in lost_units:
            count = len(lost_units.get(unit_type, []))

            minerals = self.unit_values.minerals(unit_type) * count
            gas = self.unit_values.gas(unit_type) * count

            lost_minerals += minerals
            lost_gas += gas

        return lost_minerals, lost_gas

    async def on_end(self, game_result: Result):
        self.print_contents()

    def print_contents(self):
        self.print_end(f"My lost units minerals and gas: {self.calculate_own_lost_resources()}")

        self.print_end(f"Enemy lost units minerals and gas: {self.calculate_enemy_lost_resources()}")

    def print_end(self, msg: str):
        self.knowledge.print(msg, "LostUnitsContents", stats=False)

    def get_own_enemy_lost_units(self) -> Tuple[Dict[UnitTypeId, List[Unit]], Dict[UnitTypeId, List[Unit]]]:
        """Get tuple with own and enemy lost units"""
        return (self._my_lost_units, self._enemy_lost_units)
