from enum import IntEnum
from typing import Set, Dict, Any

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sharpy.managers import ManagerBase


class GameVersion(IntEnum):
    V_4_11_4 = 78285
    V_4_11_0 = 77379
    V_4_10_0 = 75689


class VersionManager(ManagerBase):
    def __init__(self):
        self.short_version = "0.0.0"
        self.full_version = "0.0.0.12345"
        self.base_version = 12345
        self.disabled_upgrades: Set[UpgradeId] = set()
        self.moved_upgrades: Dict[UpgradeId, UnitTypeId] = {}
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        response = await self.client.ping()
        self.full_version = response.ping.game_version
        self.base_version = response.ping.base_build
        splits = response.ping.game_version.split(".")

        if len(splits) == 4:
            self.short_version = f"{splits[0]}.{splits[1]}.{splits[2]}"

        self.knowledge.print(self.full_version, "Version")
        self.configure_enums()
        self.configure_upgrades()

    async def update(self):
        pass

    async def post_update(self):
        pass

    def configure_enums(self):
        if self.base_version == GameVersion.V_4_10_0:
            self._set_enum_mapping(
                UnitTypeId,
                {
                    UnitTypeId.ASSIMILATORRICH: 1955,
                    UnitTypeId.EXTRACTORRICH: 1956,
                    UnitTypeId.INHIBITORZONESMALL: 1957,
                    UnitTypeId.INHIBITORZONEMEDIUM: 1958,
                    UnitTypeId.INHIBITORZONELARGE: 1959,
                    UnitTypeId.REFINERYRICH: 1960,
                    UnitTypeId.MINERALFIELD450: 1961,
                },
            )

    def _set_enum_mapping(self, enum: Any, items: Dict[Any, int]):
        for enum_key, value in items.items():
            enum_key._value_ = value
            enum._member_map_[enum_key.name] = value
            enum._value2member_map_[value] = enum_key
            self.print(f"Setting {enum_key.name} to {enum_key.value}")

    def configure_upgrades(self):
        if self.base_version < GameVersion.V_4_11_0:
            self.disabled_upgrades.add(UpgradeId.LURKERRANGE)
            self.disabled_upgrades.add(UpgradeId.MICROBIALSHROUD)
            self.disabled_upgrades.add(UpgradeId.VOIDRAYSPEEDUPGRADE)
            self.moved_upgrades[UpgradeId.MEDIVACINCREASESPEEDBOOST] = UnitTypeId.STARPORTTECHLAB
            self.moved_upgrades[UpgradeId.LIBERATORAGRANGEUPGRADE] = UnitTypeId.STARPORTTECHLAB
