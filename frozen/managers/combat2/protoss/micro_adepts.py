from typing import Dict

from sc2 import UnitTypeId
from frozen.managers.combat2 import GenericMicro

high_priority: Dict[UnitTypeId, int] = {
    # Terran
    UnitTypeId.MULE: 9,
    UnitTypeId.SCV: 9,

    UnitTypeId.SIEGETANK: 3,
    UnitTypeId.SIEGETANKSIEGED: 5,  # sieged tanks are much higher priority than unsieged
    UnitTypeId.GHOST: 10,
    UnitTypeId.REAPER: 8,
    UnitTypeId.MARAUDER: 4,
    UnitTypeId.MARINE: 8,
    UnitTypeId.CYCLONE: 4,
    UnitTypeId.HELLION: 8,
    UnitTypeId.HELLIONTANK: 3,
    UnitTypeId.THOR: 3,
    UnitTypeId.MEDIVAC: -1,
    UnitTypeId.VIKINGFIGHTER: -1,
    UnitTypeId.VIKINGASSAULT: -1,
    UnitTypeId.LIBERATORAG: -1,
    UnitTypeId.LIBERATOR: -1,
    UnitTypeId.RAVEN: -1,
    UnitTypeId.BATTLECRUISER: -1,

    UnitTypeId.MISSILETURRET: 1,
    UnitTypeId.BUNKER: 2,

    # Zerg
    UnitTypeId.DRONE: 9,
    UnitTypeId.ZERGLING: 8,
    UnitTypeId.BANELING: 10,
    UnitTypeId.ULTRALISK: 4,
    UnitTypeId.QUEEN: 6,
    UnitTypeId.ROACH: 4,
    UnitTypeId.RAVAGER: 4,
    UnitTypeId.HYDRALISK: 8,
    UnitTypeId.HYDRALISKBURROWED: 8,
    UnitTypeId.LURKERMP: 3,
    UnitTypeId.LURKERMPBURROWED: 3,
    UnitTypeId.INFESTOR: 10,
    UnitTypeId.BROODLORD: -1,
    UnitTypeId.MUTALISK: -1,
    UnitTypeId.CORRUPTOR: -1,
    UnitTypeId.INFESTEDTERRAN: 1,


    UnitTypeId.LARVA: -1,
    UnitTypeId.EGG: -1,
    UnitTypeId.LOCUSTMP: -1,

    # Protoss
    UnitTypeId.SENTRY: 9,
    UnitTypeId.PROBE: 10,
    UnitTypeId.HIGHTEMPLAR: 10,
    UnitTypeId.DARKTEMPLAR: 9,
    UnitTypeId.ADEPT: 8,
    UnitTypeId.ZEALOT: 8,
    UnitTypeId.STALKER: 4,
    UnitTypeId.IMMORTAL: 2,
    UnitTypeId.COLOSSUS: 3,
    UnitTypeId.ARCHON: 4,

    UnitTypeId.SHIELDBATTERY: 1,
    UnitTypeId.PHOTONCANNON: 1,
    UnitTypeId.PYLON: 2,
    UnitTypeId.FLEETBEACON: 3,

}


class MicroAdepts(GenericMicro):
    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.prio_dict = high_priority

    # TODO: Adepts shade on top of marines
    # TODO: Adepts put out a escape shade
    # TODO: Adepts shade to kill workers?
