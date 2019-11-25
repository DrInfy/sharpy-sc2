from typing import List, Dict

from frozen.knowledges import Knowledge
from frozen.combat import CombatGoal, CombatAction, EnemyData
from .state_step import StateStep
from sc2 import AbilityId
from sc2.unit import Unit


class StateRavager(StateStep):
    def __init__(self, knowledge: Knowledge):
        self.cooldown = 7.3
        super().__init__(knowledge)

        self.knowledge = knowledge
        self.used_dict: Dict[int, float] = dict()

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        time = self.ai.time
        shuffler = goal.unit.tag % 10

        if self.used_dict.get(goal.unit.tag, 0) + self.cooldown > time:
            return [command]  # Skips all else

        if enemies.enemy_power.power > 10:
            best_score = 0
            target: Unit = None
            enemy: Unit
            for enemy in enemies.close_enemies:
                d = enemy.distance_to(goal.unit)
                if d < 9:
                    score = d * 0.2 - enemy.movement_speed + enemy.radius + self.unit_values.power(enemy)
                    score += 0.1 * (enemy.tag % (shuffler + 2))

                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                self.used_dict[goal.unit.tag] = time
                return [CombatAction(goal.unit, target.position, False, AbilityId.EFFECT_CORROSIVEBILE)]

        return [command] # Skips all else