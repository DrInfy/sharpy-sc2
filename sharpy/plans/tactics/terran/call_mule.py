from typing import Optional, TYPE_CHECKING

from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class CallMule(ActBase):
    def __init__(self, on_energy=100):
        super().__init__()
        self.on_energy = on_energy

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

    async def execute(self) -> bool:
        building: Unit
        buildings = self.ai.structures(UnitTypeId.ORBITALCOMMAND).ready

        for building in buildings:
            if building.energy > self.on_energy:
                mule_target = self.solve_target()
                if mule_target is not None:
                    building(AbilityId.CALLDOWNMULE_CALLDOWNMULE, mule_target)

        return True

    def solve_target(self) -> Optional[Unit]:
        for zone in self.zone_manager.enemy_expansion_zones:  # type: Zone
            if (
                zone.is_ours
                and not zone.is_under_attack
                and zone.mineral_fields.exists
                and zone.our_townhall
                and zone.our_townhall.is_ready
            ):
                return zone.mineral_fields.random

        return None
