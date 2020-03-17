from typing import Set, Optional, Dict

from sharpy.general.extended_power import siege
from sharpy.managers.combat2.move_type import MoveType
from sc2 import Race, UnitTypeId

from sharpy.managers.combat2.micro_step import MicroStep
from sc2.position import Point2
from .action import Action
from sc2.unit import Unit
from sc2.units import Units


class CombatModel:
    StalkerToRoach = 0,  # Longer range vs shorther
    StalkerToSpeedlings = 1,  # Ranged vs melee
    StalkerToSiege = 2,  # Range vs extreme fire power
    AssaultRamp = 3,  # Push on narrow ramps
    RoachToStalker = 4,  # Shorter range vs longer

no_retreat_on_low_hp: Set[UnitTypeId] = {
    UnitTypeId.ZEALOT, UnitTypeId.ZERGLING,
    UnitTypeId.ULTRALISK, UnitTypeId.ROACH, UnitTypeId.CARRIER
}

class GenericMicro(MicroStep):
    def __init__(self, knowledge):
        self.prio_dict: Optional[Dict[UnitTypeId, int]] = None
        self.model = CombatModel.StalkerToRoach
        super().__init__(knowledge)

    def should_retreat(self, unit: Unit) -> bool:
        if unit.type_id in no_retreat_on_low_hp:
            return False

        if unit.shield_max + unit.health_max > 0:
            health_percentage = (unit.shield + unit.health) / (unit.shield_max + unit.health_max)
        else:
            health_percentage = 0

        return health_percentage < 0.3 or unit.weapon_cooldown < 0  # low hp or unit can't attack

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        self.model = CombatModel.StalkerToRoach

        if len(units.flying) == len(units):
            flyers = True
        else:
            flyers = False

        if self.move_type == MoveType.DefensiveRetreat or self.move_type == MoveType.PanicRetreat:
            return current_command

        if self.closest_group and (self.engage_ratio > 0.25 or self.can_engage_ratio > 0.25):
            # in combat
            if self.engaged_power.siege_percentage > 0.5:
                self.model = CombatModel.StalkerToSiege
            elif self.engaged_power.melee_percentage > 0.3 and not flyers:
                if self.knowledge.enemy_race == Race.Zerg and self.engaged_power.melee_power > 3:
                    self.model = CombatModel.StalkerToSpeedlings
                else:
                    if self.attack_range < self.enemy_attack_range - 0.5:
                        self.model = CombatModel.RoachToStalker
                    elif self.attack_range > self.enemy_attack_range + 0.5:
                        self.model = CombatModel.StalkerToRoach

            if self.model == CombatModel.StalkerToSpeedlings:
                if self.can_engage_ratio < 0.6:
                    # push forward
                    if self.ready_to_attack_ratio > 0.75:
                        return Action(self.closest_group.center, True)
                    if self.ready_to_attack_ratio < 0.25:
                        return Action(self.center, False)

                    # best_position = self.pather.find_weak_influence_ground(
                    #     self.center.towards(self.closest_group.center, 4), 4)

                    best_position = self.pather.find_low_inside_ground(self.center, self.closest_group.center, 6)

                    return Action(best_position, False)
                else:
                    if self.ready_to_attack_ratio > 0.75:
                        return Action(self.closest_group.center, True)
                    # best_position = self.pather.find_weak_influence_ground(
                    #     self.center.towards(self.closest_group.center, -4), 4)
                    best_position = self.pather.find_low_inside_ground(self.center, self.closest_group.center, 6)
                    return Action(best_position, False)

        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        if self.move_type == MoveType.DefensiveRetreat:
            if self.ready_to_shoot(unit):
                closest = self.closest_units.get(unit.tag, None)
                if closest and self.is_target(closest):
                    range = self.unit_values.real_range(unit, closest)
                    if range > 0 and range > unit.distance_to(closest):
                        return Action(closest, True)
            return current_command

        elif self.move_type == MoveType.PanicRetreat:
            return current_command

        if self.is_locked_on(unit) and self.enemies_near_by and not self.ready_to_shoot(unit):
            cyclones = self.enemies_near_by(UnitTypeId.CYCLONE)
            if cyclones:
                closest_cyclone = cyclones.closest_to(unit)
                backstep: Point2 = closest_cyclone.position.towards(unit.position, 15)
                if unit.is_flying:
                    backstep = self.pather.find_weak_influence_air(backstep, 4)
                else:
                    backstep = self.pather.find_weak_influence_ground(backstep, 4)
                return Action(backstep, False)

        if self.should_retreat(unit) and self.closest_group and not self.ready_to_shoot(unit):
            backstep: Point2 = unit.position.towards(self.closest_group.center, -3)
            if unit.is_flying:
                backstep = self.pather.find_weak_influence_air(backstep, 4)
            else:
                backstep = self.pather.find_weak_influence_ground(backstep, 4)
            return Action(backstep, False)

        if self.model == CombatModel.StalkerToSiege:
            siege_units = self.enemies_near_by.of_type(siege)
            if siege_units:
                target = siege_units.closest_to(unit)
                if target.distance_to(unit) < 7:
                    return Action(target, True)

        if self.model == CombatModel.StalkerToRoach:
            if self.ready_to_shoot(unit):
                if self.closest_group:
                    current_command = Action(self.closest_group.center, True)
                else:
                    current_command = Action(current_command.target, True)
            else:
                closest = self.closest_units[unit.tag]

                # d = unit.distance_to(closest)
                range = self.unit_values.real_range(unit, closest) - 0.5

                if unit.is_flying:
                    best_position = self.pather.find_low_inside_air(unit.position, closest.position, range)
                else:
                    best_position = self.pather.find_low_inside_ground(unit.position, closest.position, range)

                return Action(best_position, False)

        elif self.model == CombatModel.RoachToStalker:
            if self.ready_to_shoot(unit):
                if self.closest_group:
                    current_command = Action(self.closest_group.center, True)
                else:
                    current_command = Action(current_command.target, True)
            else:
                # Instead of backstep, move forward
                current_command = self.focus_fire(unit, current_command, self.prio_dict)
                if isinstance(current_command.target, Unit):
                    current_command.target = current_command.target.position
                    current_command.is_attack = False
                return current_command

        if self.ready_to_shoot(unit) and current_command.is_attack:
            return self.focus_fire(unit, current_command, self.prio_dict)
        return current_command
