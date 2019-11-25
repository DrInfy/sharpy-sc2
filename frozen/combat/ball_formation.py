from typing import List, Optional, Dict

from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from .combat_action import CombatAction
from .combat_goal import CombatGoal
from .enemy_data import EnemyData


class BallFormation():
    def __init__(self, knowledge):
        self.ai = knowledge.ai
        self.knowledge: 'Knowledge' = knowledge
        self.unit_values: 'UnitValue' = knowledge.unit_values
        self.our_units: Units
        self.keep_together: List[UnitTypeId] = [UnitTypeId.COLOSSUS, UnitTypeId.OBSERVER, UnitTypeId.PHOENIX]
        self.enemy_units_in_combat: Units
        self.units_in_combat: Units
        self.units_to_regroup: Units
        self.minimum_distance = 3.5


    def prepare_solve(self, our_units: Units, goal_position: Point2, combat_data: Dict[int, EnemyData], units_median: Point2):
        self.our_units = our_units

        time = self.knowledge.ai.time
        units_behind_tags = []
        units_behind_tags.clear()
        average_distance2 = 0
        wait_ended = False

        self.enemy_units_in_combat = Units([], self.ai)
        self.units_in_combat = Units([], self.ai)

        unit_count = len(our_units)
        # wait for 15% reinforcements
        wait_count = unit_count * 0.15
        if any(our_units):
            our_units = our_units.sorted_by_distance_to(goal_position)

            self.units_gather = units_median

            for unit in our_units:

                enemy_data = combat_data[unit.tag]
                if enemy_data.powered_enemies.exists:
                    self.enemy_units_in_combat.append(enemy_data.closest)
                    self.units_in_combat.append(unit)
                elif enemy_data.enemies_exist:
                    self.units_in_combat.append(unit)

    def solve_combat(self, goal: CombatGoal, command: CombatAction) -> CombatAction:
        if self.enemy_units_in_combat.exists:
            # Move in to assist closest friendly in combat
            closest_enemy = self.enemy_units_in_combat.closest_to((goal.unit))
            return CombatAction(goal.unit, closest_enemy.position, command.is_attack)

        if goal.unit.distance_to(self.units_gather) > self.minimum_distance + len(self.our_units) / 10:
            return CombatAction(goal.unit, self.units_gather, False)
        return command