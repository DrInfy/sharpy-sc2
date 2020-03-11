from sharpy.plans.acts.morph_building import MorphBuilding
from sc2 import UnitTypeId, AbilityId


class MorphLair(MorphBuilding):
    def __init__(self):
        super().__init__(UnitTypeId.HATCHERY, AbilityId.UPGRADETOLAIR_LAIR, UnitTypeId.LAIR, 1)

class MorphHive(MorphBuilding):
    def __init__(self):
        super().__init__(UnitTypeId.LAIR, AbilityId.UPGRADETOHIVE_HIVE, UnitTypeId.HIVE, 1)

