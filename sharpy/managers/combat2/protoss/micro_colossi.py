from typing import Dict

from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

high_priority: Dict[UnitTypeId, int] = {
    # Terran
    UnitTypeId.MULE: 9,
    UnitTypeId.SCV: 7,

    UnitTypeId.SIEGETANK: 3,
    UnitTypeId.SIEGETANKSIEGED: 5,  # sieged tanks are much higher priority than unsieged
    UnitTypeId.GHOST: 8,
    UnitTypeId.REAPER: 6,
    UnitTypeId.MARAUDER: 4,
    UnitTypeId.MARINE: 10,
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
    UnitTypeId.DRONE: 7,
    UnitTypeId.ZERGLING: 10,
    UnitTypeId.BANELING: 9,
    UnitTypeId.ULTRALISK: 4,
    UnitTypeId.QUEEN: 6,
    UnitTypeId.ROACH: 4,
    UnitTypeId.RAVAGER: 4,
    UnitTypeId.HYDRALISK: 9,
    UnitTypeId.HYDRALISKBURROWED: 8,
    UnitTypeId.LURKERMP: 3,
    UnitTypeId.LURKERMPBURROWED: 3,
    UnitTypeId.INFESTOR: 6,
    UnitTypeId.BROODLORD: -1,
    UnitTypeId.MUTALISK: -1,
    UnitTypeId.CORRUPTOR: -1,
    UnitTypeId.INFESTEDTERRAN: 1,


    UnitTypeId.LARVA: -1,
    UnitTypeId.EGG: -1,
    UnitTypeId.LOCUSTMP: -1,

    # Protoss
    UnitTypeId.SENTRY: 9,
    UnitTypeId.PROBE: 7,
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


class MicroColossi(MicroStep):
    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.prio_dict = high_priority

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        if self.move_type == MoveType.DefensiveRetreat:
            if self.ready_to_shoot(unit):
                closest = self.closest_units.get(unit.tag, None)
                if closest and self.is_target(closest):
                    unit_range = self.unit_values.real_range(unit, closest, self.knowledge)
                    if unit_range > 0 and unit_range > unit.distance_to(closest):
                        return Action(closest, True)
            return current_command

        elif self.move_type == MoveType.PanicRetreat:
            return current_command

        if self.ready_to_shoot(unit):
            if self.closest_group and self.closest_group.ground_units:
                current_command = Action(self.closest_group.center, True)
            else:
                current_command = Action(current_command.target, True)
        else:
            closest = self.closest_units[unit.tag]

            # d = unit.distance_to(closest)
            unit_range = self.unit_values.real_range(unit, closest, self.knowledge) - 0.5

            if unit.is_flying:
                best_position = self.pather.find_low_inside_air(unit.position, closest.position, unit_range)
            else:
                best_position = self.pather.find_low_inside_ground(unit.position, closest.position, unit_range)

            return Action(best_position, False)

        if self.ready_to_shoot(unit) and current_command.is_attack:
            return self.focus_fire(unit, current_command, self.prio_dict)
        return current_command
