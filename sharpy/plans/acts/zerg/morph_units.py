from sharpy.plans.acts import ActBase
from sharpy.plans.acts.morph_building import MorphBuilding
from sc2 import UnitTypeId, AbilityId

class MorphUnit(ActBase):
    def __init__(self, unit_type: UnitTypeId, ability_type: AbilityId, result_type: UnitTypeId,
                 cocoon_type: UnitTypeId, target_count: int):
        super().__init__()
        self.target_count = target_count
        self.result_type = result_type
        self.ability_type = ability_type
        self.unit_type = unit_type
        self.cocoon_type = cocoon_type

    async def execute(self) -> bool:
        target_count = self.cache.own(self.result_type).amount
        start_units = self.cache.own(self.unit_type).ready.sorted_by_distance_to(self.knowledge.own_main_zone.center_location)
        cocoon_units = self.cache.own(self.cocoon_type)

        target_count += len(cocoon_units)

        for target in start_units: # type: Unit
            if target.orders and target.orders[0].ability.id == self.ability_type:
                target_count += 1

        if target_count >= self.target_count:
            return True

        for target in start_units:
            if target.is_ready:
                if self.knowledge.can_afford(self.ability_type):
                    self.do(target(self.ability_type))

                self.knowledge.reserve_costs(self.ability_type)
                target_count += 1

                if target_count >= self.target_count:
                    return True
        if start_units:
            return False
        return True

class MorphRavager(MorphUnit):
    def __init__(self, target_count: int):
        super().__init__(UnitTypeId.ROACH, AbilityId.MORPHTORAVAGER_RAVAGER, UnitTypeId.RAVAGER,
            UnitTypeId.RAVAGERCOCOON, target_count)

class MorphOverseer(MorphUnit):
    def __init__(self, target_count: int):
        super().__init__(UnitTypeId.OVERLORD, AbilityId.MORPH_OVERSEER, UnitTypeId.OVERSEER,
                         UnitTypeId.OVERLORDCOCOON, target_count)

class MorphBroodLord(MorphUnit):
    def __init__(self, target_count: int):
        super().__init__(UnitTypeId.CORRUPTOR, AbilityId.MORPHTOBROODLORD_BROODLORD, UnitTypeId.BROODLORD,
                         UnitTypeId.BROODLORDCOCOON, target_count)

class MorphLurker(MorphUnit):
    def __init__(self, target_count: int):
        super().__init__(UnitTypeId.HYDRALISK, AbilityId.MORPH_LURKER, UnitTypeId.LURKERMP,
            UnitTypeId.LURKERMPEGG, target_count)

class MorphBaneling(MorphUnit):
    def __init__(self, target_count: int):
        super().__init__(UnitTypeId.ZERGLING, AbilityId.MORPHZERGLINGTOBANELING_BANELING, UnitTypeId.BANELING,
            UnitTypeId.BANELINGCOCOON, target_count)
