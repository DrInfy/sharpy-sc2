from sharpy.plans.acts.morph_building import MorphBuilding
from sc2 import UnitTypeId, AbilityId


class MorphGreaterSpire(MorphBuilding):
    def __init__(self):
        super().__init__(UnitTypeId.SPIRE, AbilityId.UPGRADETOGREATERSPIRE_GREATERSPIRE, UnitTypeId.GREATERSPIRE, 1)
