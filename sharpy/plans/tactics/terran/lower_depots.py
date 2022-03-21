from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit


class LowerDepots(ActBase):
    async def execute(self) -> bool:
        depot: Unit
        for depot in self.cache.own(UnitTypeId.SUPPLYDEPOT):
            if not self.ai.enemy_units.not_flying.closer_than(5, depot.position).exists:
                # lower depot
                depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER)

        for depot in self.cache.own(UnitTypeId.SUPPLYDEPOTLOWERED):
            if self.ai.enemy_units.not_flying.closer_than(5, depot.position).exists:
                # rise depot
                depot(AbilityId.MORPH_SUPPLYDEPOT_RAISE)

        return True
