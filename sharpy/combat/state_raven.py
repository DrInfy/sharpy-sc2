from typing import List

from sharpy.knowledges import Knowledge
from sharpy.combat import CombatGoal, CombatAction, EnemyData
from .state_step import StateStep
from sc2 import AbilityId, UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class StateRaven(StateStep):
    def __init__(self, knowledge: Knowledge):
        super().__init__(knowledge)
        self.knowledge = knowledge

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        if enemies.enemy_power.power > 10 and goal.unit.energy >= 50:
            enemy: Unit
            for enemy in enemies.close_enemies:
                if enemy.is_psionic or enemy.is_mechanical and enemy.distance_to(goal.unit) < 9.5:
                    return [CombatAction(goal.unit, enemy, False, AbilityId.EFFECT_INTERFERENCEMATRIX)]

            if goal.unit.energy >= 75 and enemies.closest.distance_to(goal.unit) < 9.5:
                return [CombatAction(goal.unit, enemies.closest, False, AbilityId.EFFECT_ANTIARMORMISSILE)]

        return [command] # Skips all else

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        ground_units: Units = enemies.our_units.not_flying
        x: Unit

        if command.ability is not None:
            return command

        if ground_units.exists:
            position: Point2 = ground_units.closest_to(goal.unit).position
            raven: Unit
            for raven in enemies.our_units(UnitTypeId.RAVEN).closer_than(5, goal.unit):
                if raven.tag != goal.unit.tag:
                    raven_position: Point2= raven.position
                    if raven_position == goal.unit.position:
                        position = position.towards_with_random_angle(self.knowledge.own_main_zone.center_location, 4)
                    else:
                        position = position.towards(raven_position, -4)

            return CombatAction(goal.unit, position, False)

        return command

