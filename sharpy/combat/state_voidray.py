from typing import List

from sharpy.knowledges import Knowledge
from sharpy.combat import CombatGoal, CombatAction, EnemyData, MoveType
from .state_step import StateStep
from sc2 import AbilityId


class StateVoidray(StateStep):
    def __init__(self, knowledge: Knowledge):
        self.cooldown = 45.1
        super().__init__(knowledge)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        time = self.ai.time
        voidray = goal.unit

        if (goal.move_type == MoveType.SearchAndDestroy or goal.move_type == MoveType.Assault):
            if self.cd_manager.is_ready(voidray.tag, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT, self.cooldown):
                close_enemies = enemies.close_enemies.closer_than(7, voidray)

                if close_enemies.exists:
                    for enemy in close_enemies:
                        if enemy.is_armored:
                            # there is a armored enemy in the vicinity
                            self.cd_manager.used_ability(voidray.tag, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT)
                            return [CombatAction(voidray, None, False, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT)]

        return [command]  # Skips all else

