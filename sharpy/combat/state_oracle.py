from typing import List, Dict

from sharpy.general.extended_power import ExtendedPower
from sc2 import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.combat import CombatGoal, CombatAction, EnemyData, MoveType
from .state_step import StateStep

offensive = { MoveType.Assault, MoveType.SearchAndDestroy, MoveType.Harass}
class StateOracle(StateStep):
    """Oracle micro for combat manager"""
    def __init__(self, knowledge):
        super().__init__(knowledge)

    def PanicRetreat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        oracle = goal.unit

        time = self.knowledge.ai.time
        if oracle.has_buff(BuffId.ORACLEWEAPON):
            return self.disable_beam(oracle)[0]

        pos = self.knowledge.pathing_manager.find_influence_air_path(oracle.position, goal.target)

        return CombatAction(oracle, pos, False)
        # enemy: Unit
        # for enemy in enemies.close_enemies.closer_than(10, oracle):
        #     if self.unit_values.air_range(enemy) > 0:
        #         air_shooter_enemies.append(enemy)
        #
        # backstep: Point2 = oracle.position.towards(goal.target, 4)
        # if air_shooter_enemies.exists:
        #     backstep = oracle.position.towards(air_shooter_enemies.center, -5)
        # return CombatAction(oracle, backstep, False)


    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        oracle = goal.unit

        if not oracle.has_buff(BuffId.ORACLEWEAPON):
            goal.ready_to_shoot = False

        air_shooter_enemies = Units([], self.ai)
        enemy: Unit

        power = ExtendedPower(self.unit_values)

        for enemy in enemies.close_enemies:
            if self.unit_values.air_range(enemy) < enemy.distance_to(oracle) + 1:
                air_shooter_enemies.append(enemy)
                power.add_unit(enemy)
                if self.unit_values.is_static_air_defense(enemy):
                    power.add(5) # can't beat turrets with oracle

        enemy_center = enemies.close_enemies.center

        for air_shooter in air_shooter_enemies:  # type: Unit
            if air_shooter.is_light and not air_shooter.is_flying:
                power.add_units(air_shooter_enemies)
            else:
                power.add_units(air_shooter_enemies * 2)

        time = self.knowledge.ai.time
        if goal.move_type == MoveType.PanicRetreat and oracle.has_buff(BuffId.ORACLEWEAPON):
            return self.disable_beam(oracle)

        possible_targets = enemies.close_enemies.filter(lambda u: not u.is_flying and not u.is_structure and u.is_light)

        if possible_targets.exists:
            if oracle.energy > 50 and possible_targets.closest_distance_to(oracle) < 5 and not oracle.has_buff(BuffId.ORACLEWEAPON):
                return self.enable_beam(oracle)

        if  power.air_power > 0 and power.air_power <= 3:
            target = air_shooter_enemies.closest_to(oracle)
            if target.is_light or target.health_percentage < 0.5:
                if not oracle.has_buff(BuffId.ORACLEWEAPON):
                    return self.enable_beam(oracle)
                # Kill the target
                return [CombatAction(oracle, target, True)]

            #target_pos = self.knowledge.pathing_manager.find_weak_influence_air(goal.target, 7)
            #move_step = self.knowledge.pathing_manager.find_influence_air_path(oracle.position, target_pos)
            return [CombatAction(oracle, target.position, True)]
        elif goal.ready_to_shoot and possible_targets:
            return [CombatAction(oracle, possible_targets.closest_to(oracle), True)]
        elif power.air_power > 12:
            # Panic retreat to whatever direction
            if goal.move_type in offensive:
                new_target: Point2 = self.knowledge.pathing_manager.find_weak_influence_air(goal.target, 7)
                step = self.knowledge.pathing_manager.find_influence_air_path(oracle.position, new_target)
                # backstep: Point2 = self.knowledge.pathing_manager.find_weak_influence_air(oracle.position, 7)
                move_action = CombatAction(oracle, step, False)
            else:
                backstep = self.knowledge.pathing_manager.find_influence_air_path(oracle.position, goal.target)
                move_action = CombatAction(oracle, backstep, False)

            # Todo disable beam?
            return [move_action]

        elif power.air_power > 3:
            # Try kiting while killing the target
            target = self.knowledge.pathing_manager.find_weak_influence_air(goal.target, 7)
            backstep = self.knowledge.pathing_manager.find_influence_air_path(oracle.position, target)

            if goal.move_type in offensive:
                move_action = CombatAction(oracle, backstep, False)
            else:
                move_action = CombatAction(oracle, backstep, False)

            if oracle.has_buff(BuffId.ORACLEWEAPON):
                if possible_targets:
                    closest = possible_targets.closest_to(oracle)
                    if closest.distance_to(oracle) < 5:
                        return [CombatAction(oracle, closest, True)]
                return [CombatAction(oracle, command.target, True), move_action]
            else:
                return [move_action]


        if possible_targets.exists:
            return [CombatAction(oracle, command.target, True)]
        else:
            return [CombatAction(oracle, command.target, False)]

    def enable_beam(self, oracle):
        self.knowledge.print("[ORACLE] beam activated")
        return [CombatAction(oracle, None, False, AbilityId.BEHAVIOR_PULSARBEAMON)]

    def disable_beam(self, oracle):
        self.knowledge.print("[ORACLE] beam disabled")
        return [CombatAction(oracle, None, False, AbilityId.BEHAVIOR_PULSARBEAMOFF)]
