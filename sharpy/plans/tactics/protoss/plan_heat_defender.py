from typing import List

from sc2.units import Units
from sharpy.managers.combat2 import MoveType

from sharpy.plans.acts import ActBase
from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge
import sc2
from sc2 import UnitTypeId


class PlanHeatDefender(ActBase):
    def __init__(self):
        super().__init__()
        self.adept_tag = None
        self.tag_shift_used_dict = {}
        self.cooldown = 11.5

        self.phaseshift_tags: List[int] = []

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.roles = self.knowledge.roles
        self.combat.use_unit_micro = False
        self.check_zones = [self.knowledge.expansion_zones[0], self.knowledge.expansion_zones[1],
                            self.knowledge.expansion_zones[2]]
        self.gather_point = self.knowledge.base_ramp.top_center.towards(self.knowledge.base_ramp.bottom_center, -4)

    async def execute(self) -> bool:

        if self.adept_tag is None:
            adepts: Units = self.knowledge.roles.free_units()(UnitTypeId.ADEPT)
            if adepts.exists:
                adept = adepts.first
                self.adept_tag = adept.tag
                self.roles.set_task(UnitTask.Reserved, adept)
                await self.assault_hot_spot(adept)
        else:
            adept = self.cache.by_tag(self.adept_tag)
            if adept is None:
                self.adept_tag = None
            else:
                await self.assault_hot_spot(adept)

        self.combat.execute()

        return True # never block

    async def assault_hot_spot(self, adept):
        ground_enemies = self.knowledge.known_enemy_units_mobile.not_flying
        if ground_enemies.exists:
            closest = ground_enemies.closest_to(adept)
            if self.tag_shift_used_dict.get(adept.tag, 0) + self.cooldown < self.knowledge.ai.time:
                self.tag_shift_used_dict[adept.tag] = self.knowledge.ai.time
                self.do(adept(sc2.AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT, closest.position))
            else:
                self.combat.add_unit(adept)
                shades = self.knowledge.ai.units(UnitTypeId.ADEPTPHASESHIFT)

                for shade in shades.tags_in(self.phaseshift_tags):
                    self.combat.add_unit(shade)

                for shade in shades.tags_not_in(self.phaseshift_tags) .closer_than(6, adept):
                    self.phaseshift_tags.append(shade.tag)
                    self.combat.add_unit(shade)

                self.combat.execute(closest.position, MoveType.SearchAndDestroy)
        else:
            hot_spot = self.knowledge.heat_map.get_zones_hotspot(self.check_zones)
            if hot_spot is None:
                hot_spot = self.gather_point

            self.combat.add_unit(adept)
            self.combat.execute(hot_spot, MoveType.SearchAndDestroy)
