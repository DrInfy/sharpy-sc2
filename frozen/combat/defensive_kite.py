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


class DefensiveKite(StateStep):
    no_retreat_on_low_hp: List[UnitTypeId] = [UnitTypeId.ZEALOT, UnitTypeId.ZERGLING, UnitTypeId.CARRIER]
    retreat_on_low_hp: List[UnitTypeId] = [UnitTypeId.SENTRY, UnitTypeId.COLOSSUS]

    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.override_kite = False

    def should_retreat(self, unit: Unit, health_percentage: float) -> bool:
        if unit.type_id in DefensiveKite.no_retreat_on_low_hp:
            return False
        return health_percentage < 0.3 or unit.weapon_cooldown < 0  # low hp or unit can't attack

        # return  (unit.type_id in DefensiveKite.retreat_on_low_hp and health_percentage < 0.5)\
        #         or unit.weapon_cooldown < 0  # unit can't attack

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        enemy = enemies.closest
        retreat = False

        if goal.move_type == MoveType.PanicRetreat or self.unit_values.defense_value(enemy.type_id) == 0:
            return []

        unit: Unit = goal.unit
        unit_pos: Point2 = unit.position

        # Take into account both unit's radius
        my_range = self.unit_values.real_range(unit, enemy, self.knowledge)
        enemy_range = self.unit_values.real_range(enemy, unit, self.knowledge)

        # This is from unit's center to enemy's center.
        distance = enemy.distance_to(unit)

        if unit.shield_max + unit.health_max > 0:
            hp = (unit.shield + unit.health) / (unit.shield_max + unit.health_max)
        else:
            hp = 0

        if goal.ready_to_shoot and goal.move_type == MoveType.DefensiveRetreat and distance < my_range:
            # This needs to be an attack, or defensive retreat will never shoot
            return [CombatAction(unit, command.target, True)]

        if not command.is_attack \
                or (not self.override_kite and (my_range < 1 or not self.unit_values.should_kite(unit.type_id))):
            return []

        if self.should_retreat(unit, hp):
            retreat = True
        elif enemy_range > my_range - 0.5 and enemy.movement_speed > unit.movement_speed:
            # Enemy is faster and has longer range, no kite
            return []

        # if distance > my_range - 0.5:
        #     # Enemy is barely in range
        #     return []


        if not unit.is_flying and enemies.my_height < enemies.enemy_center_height:
            # enemies are on high ground, no stutter step back
            # Idea here is to push forward on ramps
            # not flying enemies are ignored
            return []

        if command.is_attack:
            if retreat:
                backstep: Point2 = unit_pos.towards(enemies.enemy_center, -3)
            else:
                backstep: Point2 = enemy.position.towards(unit.position, my_range)
                if unit.distance_to(backstep) < 0.5:
                    # Unit is in desired position, prepare to shoot
                    return []

            backstep = self.correct_backstep(backstep, unit)

            if unit.type_id in self.unit_values.worker_types:
                # Mineral walk for workers, related to worker defense
                angle = sc2math.line_angle(unit_pos, backstep)
                best_angle = sc2math.pi / 6
                best_mf = None

                for mf in self.ai.mineral_field: # type: Unit
                    new_angle = sc2math.line_angle(unit_pos, mf.position)
                    angle_distance = sc2math.angle_distance(angle, new_angle)
                    if angle_distance < best_angle:
                        best_mf = mf
                        best_angle = angle_distance

                if best_mf:
                    # Use backstep with gather command to pass through own units
                    return [command, CombatAction(unit, best_mf, False, ability=AbilityId.HARVEST_GATHER)]

            return [command, CombatAction(unit, backstep, False)]

        return []
        #return [CombatAction(unit, enemy.position, True), command]

    def correct_backstep(self, backstep: Point2, unit: Unit):
        """ Corrects back step to be inside game area"""
        if not unit.is_flying and not self.ai.in_pathing_grid(backstep):
            unit_pos: Point2 = unit.position
            vector = backstep - unit_pos
            angle = sc2math.point_angle(vector)
            backstep_left = None
            backstep_right = None

            for adjust in range(1, 6):
                angle_adjust = adjust * 0.5
                new_angle = angle + angle_adjust
                if backstep_right is None:
                    adjusted_position = unit_pos + sc2math.point_from_angle(new_angle) * 3

                    if self.ai.in_pathing_grid(adjusted_position):
                        backstep_right = adjusted_position

                if backstep_left is None:
                    adjusted_position = unit_pos + sc2math.point_from_angle(-new_angle) * 3

                    if self.ai.in_pathing_grid(adjusted_position):
                        backstep_left = adjusted_position

            if backstep_left is not None and backstep_right is not None:
                if (self.knowledge.enemy_units_manager.danger_value(unit, backstep_left) <
                        self.knowledge.enemy_units_manager.danger_value(unit, backstep_right)):
                    backstep = backstep_left
                else:
                    backstep = backstep_right
            elif backstep_left is not None:
                backstep = backstep_left
            elif backstep_right is not None:
                backstep = backstep_right
        return backstep
