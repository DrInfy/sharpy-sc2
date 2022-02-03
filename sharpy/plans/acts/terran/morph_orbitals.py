from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts.morph_building import MorphBuilding
from sc2.ids.unit_typeid import UnitTypeId


class MorphOrbitals(MorphBuilding):
    def __init__(self, target_count: int = 99):
        super().__init__(
            UnitTypeId.COMMANDCENTER, AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND, UnitTypeId.ORBITALCOMMAND, target_count
        )
