from sharpy.plans.acts import ActUnit
from sc2 import UnitTypeId
from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM


class TerranUnit(ActUnit):
    def __init__(self, unit_type: UnitTypeId, to_count: int = 9999, priority: bool = False, only_once: bool = False):
        production_units: set = UNIT_TRAINED_FROM.get(unit_type, {UnitTypeId.GATEWAY})

        if unit_type == UnitTypeId.SCV:
            super().__init__(unit_type, UnitTypeId.COMMANDCENTER, to_count, priority)
        else:
            super().__init__(unit_type, list(production_units)[0], to_count, priority)
        self.only_once = only_once


    def get_unit_count(self) -> int:
        count = super().get_unit_count()

        if self.only_once:
            count += self.knowledge.lost_units_manager.own_lost_type(self.unit_type)
        return count
