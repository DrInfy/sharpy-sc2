from typing import List, Optional

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit

from .combat_action import CombatAction
from .combat_goal import CombatGoal
from .enemy_data import EnemyData
from .state_step import StateStep


class EnemyTargeting(StateStep):
    focus_workers = False
    armored_bonus = [UnitTypeId.VOIDRAY, UnitTypeId.IMMORTAL, UnitTypeId.STALKER]
    light_bonus = [UnitTypeId.COLOSSUS, UnitTypeId.ADEPT, UnitTypeId.PHOENIX, UnitTypeId.ORACLE]
    biological_bonus = [UnitTypeId.ARCHON]
    no_targeting = {UnitTypeId.EGG, UnitTypeId.LARVA, UnitTypeId.DISRUPTORPHASED, UnitTypeId.ADEPTPHASESHIFT,
                    UnitTypeId.KD8CHARGE, UnitTypeId.INTERCEPTOR}

    def get_ground_lookup_range(self, unit: Unit) -> float:
        ground_range = self.unit_values.ground_range(unit, self.knowledge)

        if ground_range <= 0:
            return 0

        if unit.type_id == UnitTypeId.ORACLE:
            return 10
        if unit.type_id == UnitTypeId.COLOSSUS:
            return 10
        elif unit.type_id == UnitTypeId.PHOENIX:
            return 15
        elif ground_range < 3:
            return ground_range + 1
        else:
            return ground_range + 2

    def get_air_lookup_range(self, unit: Unit) -> float:
        air_range = self.unit_values.air_range(unit)

        if air_range < 1:
            return 0

        return air_range

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        if not enemies.close_enemies.exists:
            return []

        # my_range = self.unit_values.ground_range(goal.unit, self.ai)
        # my_range_squared = my_range * my_range
        # my_range_air = self.unit_values.air_range(goal.unit)
        my_pos: Point2 = goal.unit.position

        lookup_range = self.get_ground_lookup_range(goal.unit)
        lookup_range_air = self.get_air_lookup_range(goal.unit)
        #enemy_candidates = enemies.close_enemies.closer_than(lookup_range, goal.unit)

        current_score = 0
        target: Optional[Unit] = None
        last_target = self.last_targeted(goal.unit)

        enemy: Unit
        for enemy in enemies.close_enemies:
            range = my_pos.distance_to(enemy.position)

            if enemy.is_flying and lookup_range_air < range:
                continue # Can't shoot.

            if not enemy.is_flying and enemy.type_id != UnitTypeId.COLOSSUS and lookup_range < range:
                continue # Can't shoot.

            if enemy.type_id in EnemyTargeting.no_targeting:
                continue  # Please don't... :facepalm:

            if enemy.is_structure and goal.unit.type_id in [UnitTypeId.ORACLE, UnitTypeId.ADEPT, UnitTypeId.DISRUPTORPHASED]:
                continue  # no point in trying

            score = self.unit_values.defense_value(enemy.type_id)

            if enemy.is_armored and goal.unit.type_id in EnemyTargeting.armored_bonus:
                score = score * 1.5

            if enemy.is_light and goal.unit.type_id in EnemyTargeting.light_bonus:
                score = score * 10  # huge bonus because light units are usually low value otherwise

            if enemy.is_biological and goal.unit.type_id in EnemyTargeting.biological_bonus:
                score = score * 1.5

            if goal.unit.is_flying and enemy.air_range > 0:
                score *= 2.0

            max = enemy.health_max + enemy.shield_max
            if max > 0:
                percentage = (enemy.health + enemy.shield) / max
            else:
                percentage = 1
            score = score * (1.75 - percentage)

            if self.focus_workers and self.unit_values.is_worker(enemy):
                score = score * 3 + 2

            if enemy.is_repairing:  # TODO: Does not actually work !!!
                score = score * 4
            if last_target == enemy.tag:
                score = score * 2 # Preference to target that the unit has already started shooting at

            if goal.unit.type_id == UnitTypeId.COLOSSUS and enemy.is_structure:
                score -= 20

            if not enemy.is_visible:
                score -= 2

            score *= (100 - range) / 100

            if score > 0 and range < self.unit_values.real_range(goal.unit, enemy, self.knowledge):
                score = score * 10 # strong preference to targets that we can actually shoot

            if score > current_score:
                current_score = score
                target = enemy

        if target is not None:
            return [CombatAction(goal.unit, target, True)]

        return []

    def last_targeted(self, unit: Unit) -> Optional[int]:

        if unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action = unit.orders[0]
            # targeting unit
            if isinstance(current_action.target, int):
                # tag found
                return current_action.target
        return None