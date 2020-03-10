from sharpy.plans.acts.morph_building import MorphBuilding
from sc2 import UnitTypeId, AbilityId


class MorphPlanetary(MorphBuilding):
    def __init__(self, target_count: int = 99):
        super().__init__(UnitTypeId.COMMANDCENTER, AbilityId.UPGRADETOPLANETARYFORTRESS_PLANETARYFORTRESS, UnitTypeId.PLANETARYFORTRESS, target_count)
