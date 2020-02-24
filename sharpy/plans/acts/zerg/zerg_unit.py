from typing import Optional

from sharpy.plans import BuildOrder
from sharpy.plans.acts import ActUnit
from sc2 import UnitTypeId
from sharpy.plans.acts.zerg.morph_units import MorphUnit, MorphRavager, MorphBroodLord, MorphOverseer, MorphBaneling, MorphLurker


class ZergUnit(BuildOrder):
    morph_unit: Optional[MorphUnit]
    act_unit: ActUnit

    def __init__(self, unit_type: UnitTypeId, to_count: int = 9999, priority: bool = False, only_once: bool = False):
        # Change this to adjust unit counts
        self._original_to_count = to_count
        self.to_count = to_count
        self.only_once = only_once

        if unit_type == UnitTypeId.BANELING:
            self.morph_unit = MorphBaneling(to_count)
        elif unit_type == UnitTypeId.LURKERMP:
            self.morph_unit = MorphLurker(to_count)
        elif unit_type == UnitTypeId.BROODLORD:
            self.morph_unit = MorphBroodLord(to_count)
        elif unit_type == UnitTypeId.RAVAGER:
            self.morph_unit = MorphRavager(to_count)
        elif unit_type == UnitTypeId.OVERSEER:
            self.morph_unit = MorphOverseer(to_count)
        else:
            self.morph_unit = None

        if self.morph_unit:
            self.unit_type = self.morph_unit.unit_type

        if unit_type == UnitTypeId.QUEEN:
            self.act_unit = ActUnit(unit_type, UnitTypeId.HATCHERY, to_count, priority)
        else:
            self.act_unit = ActUnit(unit_type, UnitTypeId.LARVA, to_count, priority)

        if self.morph_unit:
            super().__init__([self.morph_unit, self.act_unit])
        else:
            super().__init__([self.act_unit])

    @property
    def is_done(self) -> bool:
        if self.morph_unit:
            # TODO: Burrowed versions!
            unit_count = self.cache.own(self.morph_unit.result_type) + self.cache.own(self.morph_unit.cocoon_type)
        else:
            unit_count = self.act_unit.get_unit_count()

        if self.only_once:
            unit_count += self.knowledge.lost_units_manager.own_lost_type(self.unit_type)
        return unit_count >= self._original_to_count

    async def execute(self) -> bool:
        if self.morph_unit:
            self.act_unit.to_count = self.to_count - self.get_count(self.morph_unit.result_type)
            self.morph_unit.target_count = self.to_count
        else:
            self.act_unit.to_count = self.to_count
        return await super().execute()

