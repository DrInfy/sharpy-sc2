from typing import List

from sharpy.knowledges import Knowledge
from sharpy.combat import CombatGoal, CombatAction, EnemyData
from .state_step import StateStep
from sc2 import UnitTypeId, AbilityId


class StateViking(StateStep):
    def __init__(self, knowledge: Knowledge):
        super().__init__(knowledge)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        return [] # Skips all else

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        is_fighter = goal.unit.type_id == UnitTypeId.VIKINGFIGHTER
        if not enemies.enemies_exist:
            if is_fighter:
                return command
            else:
                return CombatAction(goal.unit, None, False, AbilityId.MORPH_VIKINGFIGHTERMODE)

        if is_fighter:
            if (not enemies.close_enemies(UnitTypeId.COLOSSUS).exists
                    and not enemies.close_enemies.flying.exists
                    and enemies.close_enemies.not_flying.exists):
                return CombatAction(goal.unit, None, False, AbilityId.MORPH_VIKINGASSAULTMODE)
        else:
            if enemies.enemy_power.air_presence > 0 or enemies.close_enemies(UnitTypeId.COLOSSUS).exists:
                return CombatAction(goal.unit, None, False, AbilityId.MORPH_VIKINGFIGHTERMODE)

        return command
