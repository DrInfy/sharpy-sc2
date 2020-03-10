from sharpy.plans.acts.morph_building import MorphBuilding
from sc2 import UnitTypeId, AbilityId


class MorphOrbitals(MorphBuilding):
    def __init__(self, target_count: int = 99):
        super().__init__(UnitTypeId.COMMANDCENTER, AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND, UnitTypeId.ORBITALCOMMAND, target_count)
