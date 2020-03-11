from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit


class LowerDepots(ActBase):

    async def execute(self) -> bool:
        depot: Unit
        for depot in self.cache.own(UnitTypeId.SUPPLYDEPOT):
            if not self.knowledge.known_enemy_units_mobile.not_flying.closer_than(5, depot.position).exists:
                # lower depot
                self.do(depot(AbilityId.MORPH_SUPPLYDEPOT_LOWER))


        for depot in self.cache.own(UnitTypeId.SUPPLYDEPOTLOWERED):
            if self.knowledge.known_enemy_units_mobile.not_flying.closer_than(5, depot.position).exists:
                # rise depot
                self.do(depot(AbilityId.MORPH_SUPPLYDEPOT_RAISE))

        return True
