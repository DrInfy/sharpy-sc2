from typing import List

from frozen import sc2math
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit

from .combat_action import CombatAction
from .combat_goal import CombatGoal
from .enemy_data import EnemyData
from .move_type import MoveType
from .state_step import StateStep


class OffensivePush(StateStep):
    never_push: List[UnitTypeId] = [UnitTypeId.SENTRY, UnitTypeId.COLOSSUS, UnitTypeId.DISRUPTOR]

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:

        if goal.move_type == MoveType.PanicRetreat:
            return []



        unit: Unit = goal.unit
        my_range = self.unit_values.ground_range(unit, self.knowledge)
        enemy_range = self.unit_values.ground_range(enemies.closest, self.knowledge)

        move_type: MoveType = goal.move_type
        target: Point2 = goal.target
        unit_pos: Point2 = unit.position

        durability = (unit.shield + unit.health) / (unit.health_max + unit.shield_max)
        if unit.is_flying or unit.type_id in OffensivePush.never_push:
            return []  # Flying units don't use offensive push

        if (enemies.closest.is_structure
                or (enemies.my_height < enemies.enemy_center_height and enemies.my_height < enemies.closest_height)):
            # enemy is structure or
            # enemies are on high ground, let's push forward
            # Idea here is to push forward on ramps
            pass
        elif command.is_attack:
            # Don't push against dangerous enemies with less range
            if not enemies.our_power.is_enough_for(enemies.enemy_power, 0.25) and not enemies.worker_only:
                return []  # don't push bigger or equal army
            # TODO: if we have advantage and enemy is running away or might run away
            #return []

        # if my_range > enemy_range and self.unit_values.defense_value(enemies.closest.type_id) > 0:
        #     return [] # Don't push against dangerous enemies with less range

        if durability < 0.35 or not self.unit_values.should_kite(unit.type_id):
            return []  # No sense in pushing if dying


        # if enemies.closest.distance_to(unit) < 3:
        #     return []

        if command.is_attack:
            range = min(enemies.closest.radius + unit.radius, 3)
            step: Point2 = enemies.closest.position.towards(unit_pos, range)

            if enemies.worker_only and unit.type_id == self.knowledge.my_worker_type:
                # Mineral walk for workers, related to worker defense
                target_position: Point2 = enemies.closest.position
                angle = sc2math.line_angle(unit_pos, target_position)
                best_angle = sc2math.pi / 6
                best_mf = None

                for mf in self.ai.mineral_field:  # type: Unit
                    new_angle = sc2math.line_angle(unit_pos, mf.position)
                    angle_distance = sc2math.angle_distance(angle, new_angle)
                    if angle_distance < best_angle and mf.distance_to(unit) < 10:
                        best_mf = mf
                        best_angle = angle_distance

                if best_mf:
                    if my_range + unit.radius * 2 > target_position.distance_to(unit) < 6:
                        return [CombatAction(unit, best_mf, False, ability=AbilityId.HARVEST_GATHER)]
                    # Use backstep with gather command to pass through own units
                    return [command, CombatAction(unit, best_mf, False, ability=AbilityId.HARVEST_GATHER)]

            if unit.distance_to(step) < 0.5:
                # Unit is in desired position, prepare to shoot
                return [command]
            return [command, CombatAction(unit, step, False)]

        return [CombatAction(unit, enemies.closest.position, True), command]