from typing import List

from frozen.knowledges import Knowledge
from .state_step import StateStep
from frozen.combat import CombatGoal, CombatAction, EnemyData
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class StateMedivac(StateStep):
    def __init__(self, knowledge: Knowledge):
        super().__init__(knowledge)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        return [command] # Skips all else

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        ground_units: Units = enemies.our_units.not_flying
        x: Unit

        healable_targets = enemies.our_units.filter(lambda x:
                                                    (x.health_percentage < 1 and not x.is_flying
                                                     and (x.is_biological or x.type_id == UnitTypeId.HELLIONTANK)))
        if healable_targets.exists:
            return CombatAction(goal.unit, healable_targets.closest_to(goal.unit), False, AbilityId.MEDIVACHEAL_HEAL)
        if ground_units.exists:
            position: Point2 = ground_units.closest_to(goal.unit).position
            medivac: Unit
            for medivac in enemies.our_units(UnitTypeId.MEDIVAC).closer_than(5, goal.unit):
                if medivac.tag != goal.unit.tag:
                    raven_position: Point2 = medivac.position
                    if raven_position == goal.unit.position:
                        position = position.towards_with_random_angle(self.knowledge.own_main_zone.center_location, 4)
                    else:
                        position = position.towards(raven_position, -4)

            return CombatAction(goal.unit, position, False)

        return command

