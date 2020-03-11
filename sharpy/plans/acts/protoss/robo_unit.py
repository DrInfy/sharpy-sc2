from sharpy.plans.acts import ActUnit
from sc2 import UnitTypeId


class RoboUnit(ActUnit):
    def __init__(self, unit_type: UnitTypeId, to_count: int = 9999, priority: bool = False, only_once: bool = False):
        super().__init__(unit_type, UnitTypeId.ROBOTICSFACILITY, to_count, priority)
        self.only_once = only_once

    def get_unit_count(self) -> int:
        count = super().get_unit_count()

        if self.only_once:
            count += self.knowledge.lost_units_manager.own_lost_type(self.unit_type)
        return count
