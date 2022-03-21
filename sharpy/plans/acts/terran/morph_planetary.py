from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts.morph_building import MorphBuilding
from sc2.ids.unit_typeid import UnitTypeId


class MorphPlanetary(MorphBuilding):
    def __init__(self, target_count: int = 99):
        super().__init__(
            UnitTypeId.COMMANDCENTER,
            AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS,
            UnitTypeId.PLANETARYFORTRESS,
            target_count,
        )
