import logging
from typing import Union, Optional, List, Callable, Dict

from sc2.data import Race, race_townhalls
from sharpy.general.unit_feature import UnitFeature
from sc2.constants import *
from sc2.unit import Unit
from sc2.units import Units
from .manager_base import ManagerBase
from sharpy.general.extended_power import ExtendedPower
from sharpy.interfaces import IUnitValues
from sharpy.managers.core.version_manager import GameVersion

buildings_2x2 = {
    UnitTypeId.SUPPLYDEPOT,
    UnitTypeId.PYLON,
    UnitTypeId.DARKSHRINE,
    UnitTypeId.PHOTONCANNON,
    UnitTypeId.SHIELDBATTERY,
    UnitTypeId.TECHLAB,
    UnitTypeId.STARPORTTECHLAB,
    UnitTypeId.FACTORYTECHLAB,
    UnitTypeId.BARRACKSTECHLAB,
    UnitTypeId.REACTOR,
    UnitTypeId.STARPORTREACTOR,
    UnitTypeId.FACTORYREACTOR,
    UnitTypeId.BARRACKSREACTOR,
    UnitTypeId.MISSILETURRET,
    UnitTypeId.SPORECRAWLER,
    UnitTypeId.SPIRE,
    UnitTypeId.GREATERSPIRE,
    UnitTypeId.SPINECRAWLER,
}

buildings_3x3 = {
    UnitTypeId.GATEWAY,
    UnitTypeId.WARPGATE,
    UnitTypeId.CYBERNETICSCORE,
    UnitTypeId.FORGE,
    UnitTypeId.ROBOTICSFACILITY,
    UnitTypeId.ROBOTICSBAY,
    UnitTypeId.TEMPLARARCHIVE,
    UnitTypeId.TWILIGHTCOUNCIL,
    UnitTypeId.TEMPLARARCHIVE,
    UnitTypeId.STARGATE,
    UnitTypeId.FLEETBEACON,
    UnitTypeId.ASSIMILATOR,
    UnitTypeId.ASSIMILATORRICH,
    UnitTypeId.SPAWNINGPOOL,
    UnitTypeId.ROACHWARREN,
    UnitTypeId.HYDRALISKDEN,
    UnitTypeId.BANELINGNEST,
    UnitTypeId.EVOLUTIONCHAMBER,
    UnitTypeId.NYDUSNETWORK,
    UnitTypeId.NYDUSCANAL,
    UnitTypeId.EXTRACTOR,
    UnitTypeId.EXTRACTORRICH,
    UnitTypeId.INFESTATIONPIT,
    UnitTypeId.ULTRALISKCAVERN,
    UnitTypeId.BARRACKS,
    UnitTypeId.ENGINEERINGBAY,
    UnitTypeId.FACTORY,
    UnitTypeId.GHOSTACADEMY,
    UnitTypeId.STARPORT,
    UnitTypeId.FUSIONREACTOR,
    UnitTypeId.BUNKER,
    UnitTypeId.ARMORY,
    UnitTypeId.REFINERY,
    UnitTypeId.REFINERYRICH,
}

buildings_5x5 = {
    UnitTypeId.NEXUS,
    UnitTypeId.HATCHERY,
    UnitTypeId.HIVE,
    UnitTypeId.LAIR,
    UnitTypeId.COMMANDCENTER,
    UnitTypeId.ORBITALCOMMAND,
    UnitTypeId.PLANETARYFORTRESS,
}

BUILDING_IDS = buildings_5x5.union(buildings_3x3).union(buildings_2x2)
REVERSE_MORPHS_DICT = {
    UnitTypeId.LURKERMP: UnitTypeId.HYDRALISK,
    UnitTypeId.BANELING: UnitTypeId.ZERGLING,
    UnitTypeId.RAVAGER: UnitTypeId.ROACH,
    UnitTypeId.OVERSEER: UnitTypeId.OVERLORD,
    UnitTypeId.OVERLORDTRANSPORT: UnitTypeId.OVERLORD,
    UnitTypeId.BROODLORD: UnitTypeId.CORRUPTOR,
}


class UnitData:
    def __init__(
        self,
        minerals: int,
        gas: int,
        supply: float,
        combat_value: float,
        build_time: Optional[int] = None,
        features: Optional[List[UnitFeature]] = None,
    ):
        self.minerals = minerals
        self.gas = gas
        self.supply = supply
        self.combat_value = combat_value
        self.build_time = build_time

        if features is None:
            self.features: List[UnitFeature] = []
        else:
            self.features: List[UnitFeature] = features


class UnitValue(ManagerBase, IUnitValues):
    _my_worker_type: UnitTypeId
    worker_types = {UnitTypeId.SCV, UnitTypeId.MULE, UnitTypeId.DRONE, UnitTypeId.PROBE}

    gate_types = {
        UnitTypeId.ZEALOT,
        UnitTypeId.STALKER,
        UnitTypeId.ADEPT,
        UnitTypeId.HIGHTEMPLAR,
        UnitTypeId.DARKTEMPLAR,
        UnitTypeId.SENTRY,
    }

    melee = {UnitTypeId.ZERGLING, UnitTypeId.ULTRALISK, UnitTypeId.ZEALOT}

    builders = {
        UnitTypeId.PROBE: {UnitTypeId.NEXUS},
        UnitTypeId.MOTHERSHIP: {UnitTypeId.NEXUS},
        UnitTypeId.ZEALOT: {UnitTypeId.WARPGATE, UnitTypeId.GATEWAY},
        UnitTypeId.STALKER: {UnitTypeId.WARPGATE, UnitTypeId.GATEWAY},
        UnitTypeId.ADEPT: {UnitTypeId.WARPGATE, UnitTypeId.GATEWAY},
        UnitTypeId.HIGHTEMPLAR: {UnitTypeId.WARPGATE, UnitTypeId.GATEWAY},
        UnitTypeId.DARKTEMPLAR: {UnitTypeId.WARPGATE, UnitTypeId.GATEWAY},
        UnitTypeId.SENTRY: {UnitTypeId.WARPGATE, UnitTypeId.GATEWAY},
        UnitTypeId.IMMORTAL: {UnitTypeId.ROBOTICSFACILITY},
        UnitTypeId.COLOSSUS: {UnitTypeId.ROBOTICSFACILITY},
        UnitTypeId.DISRUPTOR: {UnitTypeId.ROBOTICSFACILITY},
        UnitTypeId.WARPPRISM: {UnitTypeId.ROBOTICSFACILITY},
        UnitTypeId.OBSERVER: {UnitTypeId.ROBOTICSFACILITY},
        UnitTypeId.PHOENIX: {UnitTypeId.STARGATE},
        UnitTypeId.VOIDRAY: {UnitTypeId.STARGATE},
        UnitTypeId.ORACLE: {UnitTypeId.STARGATE},
        UnitTypeId.TEMPEST: {UnitTypeId.STARGATE},
        UnitTypeId.CARRIER: {UnitTypeId.STARGATE},
        UnitTypeId.SCV: {UnitTypeId.COMMANDCENTER, UnitTypeId.ORBITALCOMMAND, UnitTypeId.PLANETARYFORTRESS},
        UnitTypeId.MARINE: {UnitTypeId.BARRACKS},
        UnitTypeId.MARAUDER: {UnitTypeId.BARRACKS},
        UnitTypeId.REACTOR: {UnitTypeId.BARRACKS},
        UnitTypeId.GHOST: {UnitTypeId.BARRACKS},
        UnitTypeId.HELLION: {UnitTypeId.FACTORY},
        UnitTypeId.WIDOWMINE: {UnitTypeId.FACTORY},
        UnitTypeId.SIEGETANK: {UnitTypeId.FACTORY},
        UnitTypeId.CYCLONE: {UnitTypeId.FACTORY},
        UnitTypeId.THOR: {UnitTypeId.FACTORY},
        UnitTypeId.VIKING: {UnitTypeId.STARPORT},
        UnitTypeId.MEDIVAC: {UnitTypeId.STARPORT},
        UnitTypeId.LIBERATOR: {UnitTypeId.STARPORT},
        UnitTypeId.RAVEN: {UnitTypeId.STARPORT},
        UnitTypeId.BANSHEE: {UnitTypeId.STARPORT},
        UnitTypeId.BATTLECRUISER: {UnitTypeId.STARPORT},
        UnitTypeId.DRONE: {UnitTypeId.EGG},
        UnitTypeId.ZERGLING: {UnitTypeId.EGG},
        UnitTypeId.ROACH: {UnitTypeId.EGG},
        UnitTypeId.HYDRALISK: {UnitTypeId.EGG},
        UnitTypeId.MUTALISK: {UnitTypeId.EGG},
        UnitTypeId.INFESTOR: {UnitTypeId.EGG},
        UnitTypeId.CORRUPTOR: {UnitTypeId.EGG},
        UnitTypeId.OVERLORD: {UnitTypeId.EGG},
    }

    not_really_structure = {
        UnitTypeId.CREEPTUMOR,
        UnitTypeId.CREEPTUMORBURROWED,
        UnitTypeId.CREEPTUMORQUEEN,
        UnitTypeId.CREEPTUMORMISSILE,
        UnitTypeId.EGG,
    }

    build_abilities = {
        AbilityId.BUILD_SHIELDBATTERY,
        AbilityId.PROTOSSBUILD_ASSIMILATOR,
        AbilityId.PROTOSSBUILD_CYBERNETICSCORE,
        AbilityId.PROTOSSBUILD_DARKSHRINE,
        AbilityId.PROTOSSBUILD_FLEETBEACON,
        AbilityId.PROTOSSBUILD_FORGE,
        AbilityId.PROTOSSBUILD_GATEWAY,
        AbilityId.PROTOSSBUILD_NEXUS,
        AbilityId.PROTOSSBUILD_PHOTONCANNON,
        AbilityId.PROTOSSBUILD_PYLON,
        AbilityId.PROTOSSBUILD_ROBOTICSBAY,
        AbilityId.PROTOSSBUILD_ROBOTICSFACILITY,
        AbilityId.PROTOSSBUILD_STARGATE,
        AbilityId.PROTOSSBUILD_TEMPLARARCHIVE,
        AbilityId.PROTOSSBUILD_TWILIGHTCOUNCIL,
        AbilityId.TERRANBUILD_ARMORY,
        AbilityId.TERRANBUILD_BARRACKS,
        AbilityId.TERRANBUILD_BUNKER,
        AbilityId.TERRANBUILD_COMMANDCENTER,
        AbilityId.TERRANBUILD_ENGINEERINGBAY,
        AbilityId.TERRANBUILD_FACTORY,
        AbilityId.TERRANBUILD_FUSIONCORE,
        AbilityId.TERRANBUILD_GHOSTACADEMY,
        AbilityId.TERRANBUILD_MISSILETURRET,
        AbilityId.TERRANBUILD_REFINERY,
        AbilityId.TERRANBUILD_SENSORTOWER,
        AbilityId.TERRANBUILD_STARPORT,
        AbilityId.TERRANBUILD_SUPPLYDEPOT,
        AbilityId.ZERGBUILD_BANELINGNEST,
        AbilityId.ZERGBUILD_EVOLUTIONCHAMBER,
        AbilityId.ZERGBUILD_EXTRACTOR,
        AbilityId.ZERGBUILD_HATCHERY,
        AbilityId.ZERGBUILD_HYDRALISKDEN,
        AbilityId.ZERGBUILD_INFESTATIONPIT,
        AbilityId.ZERGBUILD_NYDUSNETWORK,
        AbilityId.ZERGBUILD_ROACHWARREN,
        AbilityId.ZERGBUILD_SPAWNINGPOOL,
        AbilityId.ZERGBUILD_SPINECRAWLER,
        AbilityId.ZERGBUILD_SPIRE,
        AbilityId.ZERGBUILD_SPORECRAWLER,
        AbilityId.ZERGBUILD_ULTRALISKCAVERN,
        AbilityId.BURROWDOWN_DRONE,
    }

    any_defender_types = {
        UnitTypeId.LIBERATOR,
        UnitTypeId.LIBERATORAG,
        UnitTypeId.RAVEN,
        UnitTypeId.MEDIVAC,
        UnitTypeId.WARPPRISM,
        UnitTypeId.WARPPRISMPHASING,
        UnitTypeId.HIGHTEMPLAR,
        UnitTypeId.VIPER,
        UnitTypeId.INFESTOR,
        UnitTypeId.INFESTORBURROWED,
        UnitTypeId.VIKINGFIGHTER,
        UnitTypeId.VIKINGASSAULT,
    }

    def __init__(self):
        # By storing data in the instance, can skip import conflicts.
        super().__init__()
        self.combat_ignore = {UnitTypeId.OVERLORD, UnitTypeId.LARVA} | self.not_really_structure
        self._enemy_worker_type: Optional[UnitTypeId] = None
        self.init_range_dicts()

        self.unit_data = {
            # Units
            # Terran
            UnitTypeId.SCV: UnitData(50, 0, 1, 0.5, 12, features=[UnitFeature.HitsGround]),
            UnitTypeId.MULE: UnitData(0, 0, 0, 0.01),
            UnitTypeId.MARINE: UnitData(50, 0, 1, 1, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.MARAUDER: UnitData(100, 25, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.REAPER: UnitData(50, 50, 1, 1, features=[UnitFeature.HitsGround]),
            UnitTypeId.GHOST: UnitData(150, 125, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.Cloak]),
            UnitTypeId.HELLION: UnitData(100, 0, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.HELLIONTANK: UnitData(100, 0, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.WIDOWMINE: UnitData(75, 25, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.WIDOWMINEBURROWED: UnitData(
                75, 25, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]
            ),
            UnitTypeId.SIEGETANK: UnitData(150, 125, 3, 3, features=[UnitFeature.HitsGround]),
            UnitTypeId.SIEGETANKSIEGED: UnitData(150, 125, 3, 3, features=[UnitFeature.HitsGround]),
            UnitTypeId.CYCLONE: UnitData(125, 50, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.THOR: UnitData(300, 200, 6, 6, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.VIKING: UnitData(
                150, 75, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.VIKINGASSAULT: UnitData(
                150, 75, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.VIKINGFIGHTER: UnitData(
                150, 75, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.MEDIVAC: UnitData(100, 100, 2, 2, features=[UnitFeature.Flying]),
            UnitTypeId.LIBERATOR: UnitData(
                150, 125, 3, 3, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.LIBERATORAG: UnitData(150, 125, 3, 3, features=[UnitFeature.Flying]),
            UnitTypeId.BANSHEE: UnitData(
                150, 100, 3, 3, features=[UnitFeature.HitsGround, UnitFeature.Flying, UnitFeature.Cloak]
            ),
            UnitTypeId.RAVEN: UnitData(100, 150, 2, 2, features=[UnitFeature.Flying, UnitFeature.Detector]),
            UnitTypeId.BATTLECRUISER: UnitData(
                400, 300, 6, 7, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.POINTDEFENSEDRONE: UnitData(
                0, 0, 0, 1, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]
            ),
            # Protoss
            UnitTypeId.PROBE: UnitData(50, 0, 1, 0.5, 12, features=[UnitFeature.HitsGround]),
            UnitTypeId.ZEALOT: UnitData(100, 0, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.SENTRY: UnitData(50, 100, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.STALKER: UnitData(125, 50, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.ADEPT: UnitData(100, 25, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.HIGHTEMPLAR: UnitData(50, 150, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.DARKTEMPLAR: UnitData(125, 125, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.Cloak]),
            UnitTypeId.ARCHON: UnitData(175, 275, 4, 5, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.OBSERVER: UnitData(25, 75, 1, 0.25, features=[UnitFeature.Flying, UnitFeature.Detector]),
            UnitTypeId.WARPPRISM: UnitData(250, 0, 2, 2, features=[UnitFeature.Flying]),
            UnitTypeId.IMMORTAL: UnitData(275, 100, 4, 4, features=[UnitFeature.HitsGround]),
            UnitTypeId.COLOSSUS: UnitData(300, 200, 6, 6, features=[UnitFeature.HitsGround]),
            UnitTypeId.DISRUPTOR: UnitData(150, 150, 3, 3, features=[UnitFeature.HitsGround]),
            UnitTypeId.PHOENIX: UnitData(150, 100, 2, 2, features=[UnitFeature.ShootsAir, UnitFeature.Flying]),
            UnitTypeId.VOIDRAY: UnitData(
                200, 150, 4, 4, features=[UnitFeature.Flying, UnitFeature.HitsGround, UnitFeature.ShootsAir]
            ),
            UnitTypeId.ORACLE: UnitData(150, 150, 3, 3, features=[UnitFeature.HitsGround, UnitFeature.Flying]),
            UnitTypeId.TEMPEST: UnitData(
                250, 175, 5, 5, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.CARRIER: UnitData(
                350, 250, 6, 8, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.INTERCEPTOR: UnitData(
                15, 0, 0, 0.01, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.MOTHERSHIP: UnitData(
                300, 300, 6, 6, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            # Zerg
            UnitTypeId.LARVA: UnitData(0, 0, 0, 0),
            UnitTypeId.EGG: UnitData(0, 0, 0, 0),
            UnitTypeId.DRONE: UnitData(50, 0, 1, 0.5, 12, features=[UnitFeature.HitsGround]),
            UnitTypeId.QUEEN: UnitData(150, 0, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.ZERGLING: UnitData(25, 0, 0.5, 0.5, features=[UnitFeature.HitsGround]),
            UnitTypeId.BANELINGCOCOON: UnitData(25, 25, 0.5, 1, features=[]),
            UnitTypeId.BANELING: UnitData(25, 25, 0.5, 1, features=[UnitFeature.HitsGround]),
            UnitTypeId.ROACH: UnitData(75, 25, 2, 2, features=[UnitFeature.HitsGround]),
            UnitTypeId.RAVAGER: UnitData(75 + 25, 75 + 25, 3, 3, features=[UnitFeature.HitsGround]),
            UnitTypeId.RAVAGERCOCOON: UnitData(75 + 25, 75 + 25, 3, 3, features=[]),
            UnitTypeId.HYDRALISK: UnitData(100, 50, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.LURKERMP: UnitData(
                50 + 100, 100 + 50, 3, 3, features=[UnitFeature.HitsGround, UnitFeature.Cloak]
            ),
            UnitTypeId.LURKERMPBURROWED: UnitData(
                50 + 100, 100 + 50, 3, 3, features=[UnitFeature.HitsGround, UnitFeature.Cloak]
            ),
            UnitTypeId.LURKERMPEGG: UnitData(50 + 100, 100 + 50, 3, 3, features=[]),
            UnitTypeId.INFESTOR: UnitData(100, 150, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.INFESTEDTERRAN: UnitData(0, 0, 0, 0.5, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.INFESTEDCOCOON: UnitData(0, 0, 0, 0.5, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir]),
            UnitTypeId.SWARMHOSTMP: UnitData(100, 75, 3, 3, features=[UnitFeature.HitsGround]),
            UnitTypeId.LOCUSTMP: UnitData(0, 0, 0, 0.5),
            UnitTypeId.LOCUSTMPFLYING: UnitData(0, 0, 0, 0.5),
            UnitTypeId.ULTRALISK: UnitData(275, 200, 6, 6, features=[UnitFeature.HitsGround]),
            UnitTypeId.OVERLORD: UnitData(100, 0, 0, 0.1, features=[UnitFeature.Flying]),
            UnitTypeId.OVERLORDCOCOON: UnitData(100, 0, 0, 0.1, features=[UnitFeature.Flying]),
            UnitTypeId.OVERLORDTRANSPORT: UnitData(100, 0, 0, 0.5, features=[UnitFeature.Flying]),
            UnitTypeId.TRANSPORTOVERLORDCOCOON: UnitData(100, 0, 0, 0.1, features=[UnitFeature.Flying]),
            UnitTypeId.OVERSEER: UnitData(150, 50, 0, 0.5, features=[UnitFeature.Flying, UnitFeature.Detector]),
            UnitTypeId.CHANGELING: UnitData(0, 0, 0, 0.01),
            UnitTypeId.CHANGELINGMARINE: UnitData(0, 0, 0, 0.01),
            UnitTypeId.CHANGELINGMARINESHIELD: UnitData(0, 0, 0, 0.01),
            UnitTypeId.CHANGELINGZEALOT: UnitData(0, 0, 0, 0.01),
            UnitTypeId.CHANGELINGZERGLING: UnitData(0, 0, 0, 0.01),
            UnitTypeId.CHANGELINGZERGLINGWINGS: UnitData(0, 0, 0, 0.01),
            UnitTypeId.MUTALISK: UnitData(
                100, 100, 2, 2, features=[UnitFeature.HitsGround, UnitFeature.ShootsAir, UnitFeature.Flying]
            ),
            UnitTypeId.CORRUPTOR: UnitData(150, 100, 2, 2, features=[UnitFeature.ShootsAir, UnitFeature.Flying]),
            UnitTypeId.VIPER: UnitData(100, 200, 3, 3, features=[UnitFeature.ShootsAir, UnitFeature.Flying]),
            UnitTypeId.BROODLORD: UnitData(
                150 + 150, 150 + 100, 4, 6, features=[UnitFeature.HitsGround, UnitFeature.Flying]
            ),
            UnitTypeId.BROODLORDCOCOON: UnitData(150 + 150, 150 + 100, 4, 6, features=[UnitFeature.Flying]),
            UnitTypeId.BROODLING: UnitData(0, 0, 0, 0.01),
            # Buildings
            # Terran
            UnitTypeId.COMMANDCENTER: UnitData(400, 0, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.COMMANDCENTERFLYING: UnitData(400, 0, 0, 0, None, features=[UnitFeature.Structure]),
            UnitTypeId.ORBITALCOMMAND: UnitData(150, 0, 0, 0, 25, features=[UnitFeature.Structure]),
            UnitTypeId.ORBITALCOMMANDFLYING: UnitData(150, 0, 0, 0, None, features=[UnitFeature.Structure]),
            UnitTypeId.PLANETARYFORTRESS: UnitData(
                150, 150, 0, 5, 36, features=[UnitFeature.Structure, UnitFeature.HitsGround]
            ),
            UnitTypeId.SUPPLYDEPOT: UnitData(100, 0, 0, 0, 21, features=[UnitFeature.Structure]),
            UnitTypeId.REFINERY: UnitData(75, 0, 0, 0, 21, features=[UnitFeature.Structure]),
            UnitTypeId.BARRACKS: UnitData(150, 0, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.BARRACKSFLYING: UnitData(150, 0, 0, 0, None, features=[UnitFeature.Structure]),
            UnitTypeId.ENGINEERINGBAY: UnitData(125, 0, 0, 0, 25, features=[UnitFeature.Structure]),
            # Presume that the bunker is full of marines
            UnitTypeId.BUNKER: UnitData(
                100, 0, 0, 5, 29, features=[UnitFeature.Structure, UnitFeature.ShootsAir, UnitFeature.HitsGround]
            ),
            UnitTypeId.MISSILETURRET: UnitData(
                100, 0, 0, 1, 18, features=[UnitFeature.Structure, UnitFeature.ShootsAir, UnitFeature.Detector]
            ),
            UnitTypeId.AUTOTURRET: UnitData(
                0, 0, 0, 1, None, features=[UnitFeature.Structure, UnitFeature.ShootsAir, UnitFeature.HitsGround]
            ),
            UnitTypeId.SENSORTOWER: UnitData(125, 100, 0, 0, 18, features=[UnitFeature.Structure]),
            UnitTypeId.FACTORY: UnitData(150, 100, 0, 0, 43, features=[UnitFeature.Structure]),
            UnitTypeId.FACTORYFLYING: UnitData(150, 100, 0, 0, None, features=[UnitFeature.Structure]),
            UnitTypeId.GHOSTACADEMY: UnitData(150, 50, 0, 0, 29, features=[UnitFeature.Structure]),
            UnitTypeId.ARMORY: UnitData(150, 50, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.STARPORT: UnitData(150, 100, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.STARPORTFLYING: UnitData(150, 100, 0, 0, None, features=[UnitFeature.Structure]),
            UnitTypeId.FUSIONCORE: UnitData(150, 150, 0, 0, 46, features=[UnitFeature.Structure]),
            # Terran addons
            UnitTypeId.TECHLAB: UnitData(125, 100, 0, 0, 18, features=[UnitFeature.Structure]),
            UnitTypeId.BARRACKSTECHLAB: UnitData(125, 100, 0, 0, 18, features=[UnitFeature.Structure]),
            UnitTypeId.FACTORYTECHLAB: UnitData(125, 100, 0, 0, 18, features=[UnitFeature.Structure]),
            UnitTypeId.STARPORTTECHLAB: UnitData(125, 100, 0, 0, 18, features=[UnitFeature.Structure]),
            UnitTypeId.REACTOR: UnitData(50, 50, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.BARRACKSREACTOR: UnitData(50, 50, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.FACTORYREACTOR: UnitData(50, 50, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.STARPORTREACTOR: UnitData(50, 50, 0, 0, 36, features=[UnitFeature.Structure]),
            # Protoss
            UnitTypeId.NEXUS: UnitData(400, 0, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.PYLON: UnitData(100, 0, 0, 0, 18, features=[UnitFeature.Structure]),
            UnitTypeId.ASSIMILATOR: UnitData(75, 0, 0, 0, 21, features=[UnitFeature.Structure]),
            UnitTypeId.GATEWAY: UnitData(150, 0, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.FORGE: UnitData(150, 0, 0, 0, 32, features=[UnitFeature.Structure]),
            UnitTypeId.PHOTONCANNON: UnitData(
                150,
                0,
                0,
                3,
                29,
                features=[UnitFeature.Structure, UnitFeature.ShootsAir, UnitFeature.HitsGround, UnitFeature.Detector],
            ),
            UnitTypeId.SHIELDBATTERY: UnitData(100, 0, 0, 2, 29, features=[UnitFeature.Structure]),
            UnitTypeId.WARPGATE: UnitData(150, 0, 0, 0, None, features=[UnitFeature.Structure]),
            UnitTypeId.CYBERNETICSCORE: UnitData(150, 0, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.TWILIGHTCOUNCIL: UnitData(150, 100, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.ROBOTICSFACILITY: UnitData(200, 100, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.STARGATE: UnitData(150, 150, 0, 0, 43, features=[UnitFeature.Structure]),
            UnitTypeId.TEMPLARARCHIVE: UnitData(150, 200, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.DARKSHRINE: UnitData(150, 150, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.ROBOTICSBAY: UnitData(150, 150, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.FLEETBEACON: UnitData(300, 200, 0, 0, 43, features=[UnitFeature.Structure]),
            UnitTypeId.ORACLESTASISTRAP: UnitData(
                0, 0, 0, 1, 4, features=[UnitFeature.Structure, UnitFeature.HitsGround]
            ),
            # Zerg
            UnitTypeId.HATCHERY: UnitData(300 + 50, 0, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.EXTRACTOR: UnitData(25 + 50, 0, 0, 0, 21, features=[UnitFeature.Structure]),
            UnitTypeId.SPAWNINGPOOL: UnitData(200 + 50, 0, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.EVOLUTIONCHAMBER: UnitData(75 + 50, 0, 0, 0, 25, features=[UnitFeature.Structure]),
            UnitTypeId.SPINECRAWLER: UnitData(
                100 + 50, 0, 0, 3, 36, features=[UnitFeature.Structure, UnitFeature.HitsGround]
            ),
            UnitTypeId.SPORECRAWLER: UnitData(
                75 + 50, 0, 0, 3, 21, features=[UnitFeature.Structure, UnitFeature.Detector, UnitFeature.ShootsAir]
            ),
            UnitTypeId.ROACHWARREN: UnitData(150 + 50, 0, 0, 0, 39, features=[UnitFeature.Structure]),
            UnitTypeId.BANELINGNEST: UnitData(100 + 50, 50, 0, 0, 50, features=[UnitFeature.Structure]),
            UnitTypeId.LAIR: UnitData(450 + 50, 100, 0, 0, 57, features=[UnitFeature.Structure]),
            UnitTypeId.HYDRALISKDEN: UnitData(100 + 50, 100, 0, 0, 29, features=[UnitFeature.Structure]),
            UnitTypeId.LURKERDEN: UnitData(150 + 50, 150, 0, 0, 86, features=[UnitFeature.Structure]),
            UnitTypeId.LURKERDENMP: UnitData(
                150 + 50, 150, 0, 0, 86, features=[UnitFeature.Structure]
            ),  # MP = multi-player?
            UnitTypeId.INFESTATIONPIT: UnitData(100 + 50, 100, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.SPIRE: UnitData(200 + 50, 200, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.NYDUSNETWORK: UnitData(150 + 50, 200, 0, 0, 36, features=[UnitFeature.Structure]),
            UnitTypeId.NYDUSCANAL: UnitData(50, 50, 0, 7, 14, features=[UnitFeature.Structure]),  # Nydus Worm
            UnitTypeId.HIVE: UnitData(650 + 50, 250, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.ULTRALISKCAVERN: UnitData(150 + 50, 200, 0, 0, 46, features=[UnitFeature.Structure]),
            UnitTypeId.GREATERSPIRE: UnitData(300 + 50, 350, 0, 0, 71, features=[UnitFeature.Structure]),
            UnitTypeId.CREEPTUMOR: UnitData(0, 0, 0, 0.1, 11, features=[UnitFeature.Structure, UnitFeature.Cloak]),
        }

        self.gas_miners = {UnitTypeId.ASSIMILATOR, UnitTypeId.EXTRACTOR, UnitTypeId.REFINERY}

        self.detectors: List[UnitTypeId] = []
        for unit_data_key in self.unit_data:
            unit_data = self.unit_data.get(unit_data_key)
            if UnitFeature.Detector in unit_data.features:
                self.detectors.append(unit_data_key)

    @property
    def enemy_worker_type(self) -> Optional[UnitTypeId]:
        if self._enemy_worker_type is None:
            self._enemy_worker_type = self.get_worker_type(self.ai.enemy_race)
        return self._enemy_worker_type

    @property
    def my_worker_type(self) -> Optional[UnitTypeId]:
        return self._my_worker_type

    def init_range_dicts(self):
        self._ground_range_dict: Dict[UnitTypeId, Callable[[Unit], float]] = {
            UnitTypeId.RAVEN: lambda u: 9,
            UnitTypeId.ORACLE: lambda u: 4,
            UnitTypeId.CARRIER: lambda u: 8,
            UnitTypeId.BATTLECRUISER: lambda u: 6,
            UnitTypeId.DISRUPTOR: lambda u: 10,
            UnitTypeId.BANELING: lambda u: 0.1,
            UnitTypeId.SENTRY: lambda u: 5,
            UnitTypeId.VOIDRAY: lambda u: 6,
            UnitTypeId.WIDOWMINEBURROWED: lambda u: 5,
            UnitTypeId.ORACLESTASISTRAP: lambda u: 5,
        }

        self._air_range_dict: Dict[UnitTypeId, Callable[[Unit], float]] = {
            UnitTypeId.RAVEN: lambda u: 9,
            UnitTypeId.CARRIER: lambda u: 8,
            UnitTypeId.BATTLECRUISER: lambda u: 6,
            UnitTypeId.SENTRY: lambda u: 5,
            UnitTypeId.VOIDRAY: lambda u: 6,
            UnitTypeId.WIDOWMINEBURROWED: lambda u: 5,
        }

        def lurker_range(unit: Unit):
            if self.knowledge.version_manager.base_version < GameVersion.V_4_11_0:
                return 8
            else:
                if unit.is_mine and self.ai.already_pending_upgrade(UpgradeId.LURKERRANGE) >= 1:
                    return 10
                return 8

        def cyclone_range(unit: Unit):
            if not unit.is_mine:
                return 9  # worst case
            if self.knowledge.cooldown_manager.is_ready(unit.tag, AbilityId.LOCKON_LOCKON):
                return 6
            if self.knowledge.cooldown_manager.is_ready(unit.tag, AbilityId.CANCEL_LOCKON):
                return 9
            return 6  # ?

        def colossus_range(unit: Unit):
            if not unit.is_mine:
                if self.ai.time > 6 * 60:
                    # Let's assume the worst, enemy has the upgrade!
                    return 9
                return 7

            if self.ai.already_pending_upgrade(UpgradeId.EXTENDEDTHERMALLANCE) >= 1:
                return 9
            return 7

        self._ground_range_dict[UnitTypeId.LURKERMP] = lurker_range
        self._ground_range_dict[UnitTypeId.LURKERMPBURROWED] = lurker_range
        self._ground_range_dict[UnitTypeId.COLOSSUS] = colossus_range
        self._ground_range_dict[UnitTypeId.CYCLONE] = cyclone_range
        self._air_range_dict[UnitTypeId.CYCLONE] = cyclone_range

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self._my_worker_type = self.get_worker_type(knowledge.ai.race)

    async def update(self):
        pass

    async def post_update(self):
        pass

    def should_attack(self, unit: Unit):
        """Returns boolean whether unit should participate in an attack. Ignores structures, workers and other non attacking types."""
        if unit.type_id in self.combat_ignore:
            return False
        if self.ai.race == Race.Zerg and unit.type_id == UnitTypeId.QUEEN:
            return False
        if (
            unit.type_id == UnitTypeId.INTERCEPTOR
            or unit.type_id == UnitTypeId.ADEPTPHASESHIFT
            or unit.type_id == UnitTypeId.MULE
        ):
            return False
        return not unit.is_structure and unit.type_id not in self.worker_types

    def building_start_time(self, game_time: float, type_id: UnitTypeId, build_progress: float):
        """Calculates when building construction started. This can be used to eg. detect early rushes."""
        build_time = self.build_time(type_id)
        if build_time is None:
            return None

        start_time = game_time - build_time * build_progress
        return start_time

    def building_completion_time(self, game_time: float, type_id: UnitTypeId, build_progress: float):
        start_time = self.building_start_time(game_time, type_id, build_progress)
        if start_time is None:
            return None

        completion_time = start_time + self.build_time(type_id)
        return completion_time

    def minerals(self, unit_type: UnitTypeId) -> float:
        unit = self.unit_data.get(unit_type, None)
        if unit is not None:
            return unit.minerals
        return 0

    def gas(self, unit_type: UnitTypeId) -> float:
        unit = self.unit_data.get(unit_type, None)
        if unit is not None:
            return unit.gas
        return 0

    def supply(self, unit_type: UnitTypeId) -> float:
        unit = self.unit_data.get(unit_type, None)
        if unit is not None:
            return unit.supply
        return 0

    def defense_value(self, unit_type: UnitTypeId) -> float:
        """Deprecated, don't use with main bot any more! use power instead."""
        unit = self.unit_data.get(unit_type, None)
        if unit is not None:
            return unit.combat_value
        return 1.0

    def build_time(self, unit_type: UnitTypeId) -> int:
        if unit_type == UnitTypeId.WARPGATE:
            unit_type = UnitTypeId.GATEWAY

        unit = self.unit_data.get(unit_type, None)
        if unit is not None and unit.build_time is not None:
            return unit.build_time

        return 0

    def power(self, unit: Unit) -> float:
        """Returns combat power of the unit, taking into account it's known health and shields."""
        # note: sc2.Unit.health_percentage does not include shields.
        current_health = unit.health + unit.shield
        maximum_health = unit.health_max + unit.shield_max

        if maximum_health > 0:
            health_percentage = 0.5 + 0.5 * current_health / maximum_health
        else:
            # this should only happen with known enemy structures that have is_visible=False
            health_percentage = 1

        return self.power_by_type(unit.type_id, health_percentage)

    def power_by_type(self, type_id: UnitTypeId, health_percentage: float = 1) -> float:
        unit_value = self.unit_data.get(type_id, None)
        if unit_value is not None:
            return unit_value.combat_value * health_percentage
        return 1.0 * health_percentage

    def ground_range(self, unit: Unit) -> float:
        func = self._ground_range_dict.get(unit.type_id, None)
        if func:
            return func(unit)
        return unit.ground_range

    def air_range(self, unit: Unit) -> float:
        func = self._air_range_dict.get(unit.type_id, None)
        if func:
            return func(unit)
        return unit.air_range

    def can_shoot_air(self, unit: Unit) -> bool:
        return self.air_range(unit) > 0

    def can_shoot_ground(self, unit: Unit) -> bool:
        return self.ground_range(unit) > 0

    def can_assist_defense(self, unit: Unit) -> bool:
        return unit.type_id in UnitValue.any_defender_types

    def real_range(self, unit: Unit, other: Unit) -> float:
        """Returns real range for a unit and against another unit, taking both units radius into account."""
        if other.is_flying or other.has_buff(BuffId.GRAVITONBEAM):
            corrected_range = self.air_range(unit)
        else:
            corrected_range = self.ground_range(unit)

        if corrected_range <= 0:
            return corrected_range

        # eg. stalker.radius + stalker.range + marine.radius
        return unit.radius + corrected_range + other.radius

    def real_speed(self, unit: Unit) -> float:
        type_id = unit.type_id
        # TODO: OWn speed adjustments from upgrades
        # TODO: Hydralisk, banshee, warp prism, observer, better detection for zergling speed
        speed = unit.movement_speed

        if unit.is_enemy:
            if self.knowledge.enemy_race == Race.Zerg:
                if type_id == UnitTypeId.ZERGLING:
                    if self.ai.time > 200:
                        speed = 6.58

                on_creep = self.ai.has_creep(unit.position)

                if on_creep:
                    if type_id == UnitTypeId.QUEEN:
                        return speed * 2.6667
                    if type_id == UnitTypeId.HYDRALISK:
                        return speed * 1.5
                    return speed * 1.3

        return speed

    def should_kite(self, unit_type: UnitTypeId) -> bool:
        if unit_type == UnitTypeId.VOIDRAY or unit_type == UnitTypeId.ARCHON:
            return False
        if unit_type == UnitTypeId.ZEALOT or unit_type == UnitTypeId.ZERGLING or unit_type == UnitTypeId.ULTRALISK:
            return False

        return True

    def is_worker(self, unit: Union[Unit, UnitTypeId]):
        if type(unit) is Unit:
            unit_type = unit.type_id
        else:
            unit_type = unit

        return unit_type in {UnitTypeId.SCV, UnitTypeId.MULE, UnitTypeId.DRONE, UnitTypeId.PROBE}

    @staticmethod
    def is_static_ground_defense(unit: Union[Unit, UnitTypeId]):
        """Returns true if the unit is a static ground defense. Does not consider bunkers."""
        assert unit is not None and (isinstance(unit, Unit) or isinstance(unit, UnitTypeId))
        if type(unit) is Unit:
            unit_type = unit.type_id
        else:
            unit_type = unit

        return unit_type in {
            UnitTypeId.PHOTONCANNON,
            UnitTypeId.SPINECRAWLER,
            UnitTypeId.SPINECRAWLERUPROOTED,
            UnitTypeId.PLANETARYFORTRESS,
        }

    @staticmethod
    def is_static_air_defense(unit: Union[Unit, UnitTypeId]):
        """Returns true if the unit is a static air defense. Does not consider bunkers."""
        assert unit is not None and (isinstance(unit, Unit) or isinstance(unit, UnitTypeId))
        if type(unit) is Unit:
            unit_type = unit.type_id
        else:
            unit_type = unit

        return unit_type in {
            UnitTypeId.PHOTONCANNON,
            UnitTypeId.SPORECRAWLER,
            UnitTypeId.SPORECRAWLERUPROOTED,
            UnitTypeId.MISSILETURRET,
        }

    def is_ranged_unit(self, unit: Unit):
        if unit.ground_range > 1:
            return True
        return False

    def real_type(self, unit_type: UnitTypeId):
        """Find a mapping if there is one, or use the unit_type as it is"""
        return real_types.get(unit_type, unit_type)

    @staticmethod
    def get_worker_type(race: Race) -> Optional[UnitTypeId]:
        """Returns the basic worker type of each race. Does not support Random race."""
        if race == Race.Terran:
            return UnitTypeId.SCV
        if race == Race.Protoss:
            return UnitTypeId.PROBE
        if race == Race.Zerg:
            return UnitTypeId.DRONE
        return None

    def is_townhall(self, unit_type: Union[Unit, UnitTypeId]):
        """Returns true if the unit_type or unit_type type is a main structure, ie. Command Center, Nexus, Hatchery, or one of
        their upgraded versions."""

        if isinstance(unit_type, Unit):
            final_type = unit_type.type_id
        else:
            final_type = unit_type

        all_townhall_types = race_townhalls[Race.Random]

        return final_type in all_townhall_types

    def calc_total_power(self, units: Units) -> ExtendedPower:
        """Calculates total power for the given units (either own or enemy)."""

        total_power = ExtendedPower(self)

        if not units.exists:
            return total_power

        first_owner_id = None

        for unit in units:
            if first_owner_id and unit.owner_id and not unit.owner_id == first_owner_id:
                logging.warning(
                    f"Unit owner id does not match. tag: {unit.tag} type: {unit.type_id} "
                    + f"owner id: {unit.type_id} (expected {first_owner_id}"
                )
                continue
            if unit.can_be_attacked:
                first_owner_id = unit.owner_id
            total_power.add_unit(unit)

        return total_power


real_types: Dict[UnitTypeId, UnitTypeId] = {
    # Zerg
    UnitTypeId.DRONEBURROWED: UnitTypeId.DRONE,
    UnitTypeId.ZERGLINGBURROWED: UnitTypeId.ZERGLING,
    UnitTypeId.BANELINGBURROWED: UnitTypeId.BANELING,
    UnitTypeId.BANELINGCOCOON: UnitTypeId.BANELING,
    UnitTypeId.ROACHBURROWED: UnitTypeId.ROACH,
    UnitTypeId.HYDRALISKBURROWED: UnitTypeId.HYDRALISK,
    UnitTypeId.ULTRALISKBURROWED: UnitTypeId.ULTRALISK,
    UnitTypeId.OVERLORDTRANSPORT: UnitTypeId.OVERLORD,
    UnitTypeId.OVERLORDCOCOON: UnitTypeId.OVERLORD,
    UnitTypeId.RAVAGERCOCOON: UnitTypeId.RAVAGER,
    UnitTypeId.LURKERMPBURROWED: UnitTypeId.LURKERMP,
    UnitTypeId.QUEENBURROWED: UnitTypeId.QUEEN,
    UnitTypeId.CREEPTUMORBURROWED: UnitTypeId.CREEPTUMOR,
    UnitTypeId.INFESTORBURROWED: UnitTypeId.INFESTOR,
    UnitTypeId.SPINECRAWLERUPROOTED: UnitTypeId.SPINECRAWLER,
    UnitTypeId.SPORECRAWLERUPROOTED: UnitTypeId.SPORECRAWLER,
    # Terran
    UnitTypeId.SIEGETANKSIEGED: UnitTypeId.SIEGETANK,
    UnitTypeId.VIKINGASSAULT: UnitTypeId.VIKINGFIGHTER,
    UnitTypeId.THORAP: UnitTypeId.THOR,
    UnitTypeId.LIBERATORAG: UnitTypeId.LIBERATOR,
    UnitTypeId.WIDOWMINEBURROWED: UnitTypeId.WIDOWMINE,
    UnitTypeId.SUPPLYDEPOTLOWERED: UnitTypeId.SUPPLYDEPOT,
    UnitTypeId.BARRACKSREACTOR: UnitTypeId.REACTOR,
    UnitTypeId.FACTORYREACTOR: UnitTypeId.REACTOR,
    UnitTypeId.STARPORTREACTOR: UnitTypeId.REACTOR,
    UnitTypeId.BARRACKSTECHLAB: UnitTypeId.TECHLAB,
    UnitTypeId.FACTORYTECHLAB: UnitTypeId.TECHLAB,
    UnitTypeId.STARPORTTECHLAB: UnitTypeId.TECHLAB,
    # Protoss
    UnitTypeId.WARPPRISMPHASING: UnitTypeId.WARPPRISM,
    UnitTypeId.OBSERVERSIEGEMODE: UnitTypeId.OBSERVER,
}
