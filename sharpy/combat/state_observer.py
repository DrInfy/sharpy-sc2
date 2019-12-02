from typing import List

from sharpy.knowledges import Knowledge
from sharpy.combat import CombatGoal, CombatAction, EnemyData
from .state_step import StateStep
from sc2 import UnitTypeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class StateObserver(StateStep):
    def __init__(self, knowledge: Knowledge):
        super().__init__(knowledge)
        self.knowledge = knowledge

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        return [command] # Skips all else

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        ground_units: Units = enemies.our_units.not_flying
        x: Unit

        if ground_units.exists:
            position: Point2 = ground_units.closest_to(goal.unit).position
            observer: Unit
            for observer in enemies.our_units(UnitTypeId.OBSERVER).closer_than(5, goal.unit):
                if observer.tag != goal.unit.tag:
                    observer_position: Point2 = observer.position
                    if observer_position == goal.unit.position:
                        position = position.towards_with_random_angle(self.knowledge.own_main_zone.center_location, 4)
                    else:
                        position = position.towards(observer_position, -4)

            return CombatAction(goal.unit, position, False)

        return command

