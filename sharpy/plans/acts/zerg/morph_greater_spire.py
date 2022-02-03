from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts.morph_building import MorphBuilding
from sc2.ids.unit_typeid import UnitTypeId


class MorphGreaterSpire(MorphBuilding):
    def __init__(self):
        super().__init__(UnitTypeId.SPIRE, AbilityId.UPGRADETOGREATERSPIRE_GREATERSPIRE, UnitTypeId.GREATERSPIRE, 1)
