from typing import List

from sc2 import AbilityId
from sc2.position import Point2

from sharpy.combat import CombatGoal, CombatAction, EnemyData
# from sharpy.general.combat.combat_manager import CombatManager
from .state_step import StateStep

COOLDOWN = 21.1
INTERVAL = 3
class StateDisruptor(StateStep):
    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.last_used_any = 0
        self.tags_ready: List[int] = []

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        disruptor = goal.unit
        goal.ready_to_shoot = False  # Kite away
        time = self.knowledge.ai.time

        relevant_enemies = enemies.close_enemies.not_structure.not_flying

        if time < self.last_used_any + INTERVAL or len(relevant_enemies) < 4:
            return []

        center = relevant_enemies.center

        if self.cd_manager.is_ready(disruptor.tag, AbilityId.EFFECT_PURIFICATIONNOVA):
            if center.distance_to(disruptor.position) < 11:
                self.last_used_any = time
                return [CombatAction(disruptor, center, False, AbilityId.EFFECT_PURIFICATIONNOVA)]
            else:
                goal.ready_to_shoot = True
        else:
            backstep: Point2 = disruptor.position.towards(enemies.enemy_center, -3)
            return [CombatAction(disruptor, backstep, False)]
        return []

class StatePurificationNova(StateStep):
    def __init__(self, knowledge):
        super().__init__(knowledge)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        relevant_enemies = enemies.close_enemies.not_structure.not_flying

        if relevant_enemies.exists:
            target = relevant_enemies.closest_to(enemies.enemy_center)
        else:
            target = enemies.close_enemies.closest_to(enemies.enemy_center)
        return [CombatAction(goal.unit, target, False)]
