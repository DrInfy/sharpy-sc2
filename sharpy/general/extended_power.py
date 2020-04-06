from typing import Union, List, Set

from sc2 import UnitTypeId
from sc2.unit import Unit

from sharpy.general.unit_feature import UnitFeature

melee = {
    UnitTypeId.ZERGLING,
    UnitTypeId.ULTRALISK,
    UnitTypeId.ZEALOT,
    UnitTypeId.SCV,
    UnitTypeId.PROBE,
    UnitTypeId.DRONE
}

siege = {
    # Terran
    UnitTypeId.SIEGETANKSIEGED,
    UnitTypeId.LIBERATORAG,
    UnitTypeId.CYCLONE,
    UnitTypeId.BANSHEE,
    UnitTypeId.BATTLECRUISER,
    UnitTypeId.VIKINGFIGHTER,
    # Protoss
    UnitTypeId.COLOSSUS,
    UnitTypeId.CARRIER,
    UnitTypeId.TEMPEST,
    UnitTypeId.MOTHERSHIP,
    # Zerg
    UnitTypeId.BROODLORD,
    UnitTypeId.LURKERMP,
}


class ExtendedPower:

    def is_enough_for(self, enemies: 'ExtendedPower', our_percentage: float = 1.1) -> bool:
        # reduce some variable from air / ground power so that we don't fight against 100 roach with
        # 20 stalkers and observer.
        if self.power < 1:
            return False

        if self.air_power * our_percentage >= enemies.air_presence \
            and self.ground_power * our_percentage >= enemies.ground_presence \
            and self.power * our_percentage >= enemies.power:
            return True
        return False

    def __init__(self, values: 'UnitValue'):
        self.values = values
        self.power: float = 0
        self.air_presence: float = 0
        self.ground_presence: float = 0
        self.air_power: float = 0
        self.ground_power: float = 0
        self.melee_power: float = 0
        self.siege_power: float = 0
        # count of units
        self.detectors: int = 0
        self.stealth_power: float = 0

    @property
    def melee_percentage(self) -> float:
        if self.power > 0:
            return self.melee_power / self.power
        return 0

    @property
    def siege_percentage(self) -> float:
        if self.power > 0:
            return self.siege_power / self.power
        return 0

    def add_units(self, units: Union[List[Unit], Set[Unit]]):
        for unit in units:
            self.add_unit(unit)

    def add_unit(self, unit: Union[Unit, UnitTypeId], count = 1):
        unit_type: UnitTypeId

        if type(unit) is Unit:
            pwr = self.values.power(unit)
            unit_type = unit.type_id
        else:
            assert isinstance(unit, UnitTypeId)
            pwr = self.values.power_by_type(unit, 1)
            unit_type = unit

        pwr *= count
        self.power += pwr

        unit_data = self.values.unit_data.get(unit_type, None)
        if unit_data is None:
            self.ground_presence += pwr
        else:
            features = unit_data.features

            if UnitFeature.Flying in features:
                self.air_presence += pwr
            else:
                self.ground_presence += pwr

            if UnitFeature.HitsGround in features:
                self.ground_power += pwr
                if unit_type in melee:
                    self.melee_power += pwr
            if UnitFeature.ShootsAir in features:
                if unit_type == UnitTypeId.SENTRY:
                    # Exception to the rule due to weak attack
                    self.air_power += 0.5
                else:
                    self.air_power += pwr

            if unit_type in siege:
                self.siege_power = pwr

            if UnitFeature.Cloak in features:
                self.stealth_power += pwr

            if UnitFeature.Detector in features:
                self.detectors += 1

    def add_power(self, extended_power: 'ExtendedPower'):
        self.power += extended_power.power
        self.air_presence += extended_power.air_presence
        self.ground_presence += extended_power.ground_presence
        self.air_power += extended_power.air_power
        self.ground_power += extended_power.ground_power
        self.melee_power += extended_power.melee_power
        self.siege_power += extended_power.siege_power
        # count of units
        self.detectors += extended_power.detectors
        self.stealth_power += extended_power.stealth_power

    def substract_power(self, extended_power: 'ExtendedPower'):
        self.power -= extended_power.power
        self.air_presence -= extended_power.air_presence
        self.ground_presence -= extended_power.ground_presence
        self.air_power -= extended_power.air_power
        self.ground_power -= extended_power.ground_power
        self.melee_power -= extended_power.melee_power
        self.siege_power -= extended_power.siege_power
        # count of units
        self.detectors -= extended_power.detectors
        self.stealth_power -= extended_power.stealth_power

    def add(self, value_to_add: float):
        self.power += value_to_add
        self.air_presence += value_to_add
        self.ground_presence += value_to_add
        self.air_power += value_to_add
        self.ground_power += value_to_add
        self.melee_power += value_to_add
        self.siege_power += value_to_add
        self.detectors += value_to_add
        self.stealth_power += value_to_add

    def multiply(self, multiplier: float):
        self.power *= multiplier
        self.air_presence *= multiplier
        self.ground_presence *= multiplier
        self.air_power *= multiplier
        self.ground_power *= multiplier
        self.melee_power *= multiplier
        self.siege_power *= multiplier
        self.detectors *= multiplier
        self.stealth_power *= multiplier

    def clear(self):
        self.power = 0
        self.air_presence = 0
        self.ground_presence = 0
        self.air_power = 0
        self.ground_power = 0
        self.melee_power = 0
        self.siege_power = 0
        self.detectors = 0
        self.stealth_power = 0
