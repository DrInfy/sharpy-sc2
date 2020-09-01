import warnings

from sc2 import UnitTypeId, AbilityId, Set
from sc2.ids.upgrade_id import UpgradeId

from sc2.units import Units
from .act_base import ActBase

from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sharpy.managers import VersionManager


class Tech(ActBase):
    """
    Act for researching or upgrading a technology.
    """

    equivalent_structures = {
        UnitTypeId.SPIRE: {UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE},
        UnitTypeId.GREATERSPIRE: {UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE},
        UnitTypeId.HATCHERY: {UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE},
        UnitTypeId.LAIR: {UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE},
        UnitTypeId.HIVE: {UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE},
    }

    def __init__(self, upgrade_type: UpgradeId, from_building: UnitTypeId = None):
        """
        :param upgrade_type: Upgrade to research.
        :param from_building: Optional building to research the upgrade from. This should no longer be needed,
        as the building is available through an existing mapping file. The parameter is left for backwards
        compatibility and possible SC2 version mismatches.
        """
        assert upgrade_type is not None and isinstance(upgrade_type, UpgradeId)
        self.upgrade_type: UpgradeId = upgrade_type

        if from_building is None:
            from_building = UPGRADE_RESEARCHED_FROM[self.upgrade_type]

        assert isinstance(from_building, UnitTypeId) or from_building is None

        self._from_building = from_building
        # This is used to determine if the upgrade actually exists in the current version of the game
        self.enabled = True
        self.from_buildings: Set[UnitTypeId] = set()

        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

        if self.upgrade_type in self.knowledge.version_manager.disabled_upgrades:
            # Upgrade not available in this version of the game
            self.enabled = False
            return

        version_manager: VersionManager = knowledge.version_manager

        if self._from_building is None:
            self._from_building = version_manager.moved_upgrades.get(
                self.upgrade_type, UPGRADE_RESEARCHED_FROM[self.upgrade_type]
            )

        if self._from_building in self.equivalent_structures:
            self.from_buildings = self.equivalent_structures[self._from_building]
        else:
            self.from_buildings = {self._from_building}

    async def execute(self) -> bool:
        if not self.enabled:
            return True

        builders = self.cache.own(self.from_buildings).ready

        if self.already_pending_upgrade(builders) > 0:
            return True  # Started

        cost = self.ai._game_data.upgrades[self.upgrade_type.value].cost
        creationAbilityID = self.solve_ability()

        if builders.ready.exists and self.knowledge.can_afford(self.upgrade_type):
            for builder in builders.ready:
                if len(builder.orders) == 0:
                    # todo: remove this call?
                    self.print(f"Started {self.upgrade_type.name}")
                    self.do(builder(creationAbilityID))
                    return False

        self.knowledge.reserve(cost.minerals, cost.vespene)
        return False

    def solve_ability(self) -> AbilityId:
        if self.upgrade_type == UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1:
            return AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL1
        if self.upgrade_type == UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2:
            return AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL2
        if self.upgrade_type == UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3:
            return AbilityId.ARMORYRESEARCH_TERRANVEHICLEANDSHIPPLATINGLEVEL3

        return self.ai._game_data.upgrades[self.upgrade_type.value].research_ability.id

    def already_pending_upgrade(self, builders: Units) -> float:
        if self.upgrade_type in self.ai.state.upgrades:
            return 1

        creationAbilityID = self.solve_ability()

        level = None
        if "LEVEL" in self.upgrade_type.name:
            level = self.upgrade_type.name[-1]

        for structure in builders:
            for order in structure.orders:
                if order.ability.id is creationAbilityID:
                    if level and order.ability.button_name[-1] != level:
                        return 0
                    return order.progress
        return 0


class ActTech(Tech):
    def __init__(self, upgrade_type: UpgradeId, from_building: UnitTypeId = None):
        warnings.warn("'ActTech' is deprecated, use 'Tech' instead", DeprecationWarning, 2)
        super().__init__(upgrade_type, from_building)
