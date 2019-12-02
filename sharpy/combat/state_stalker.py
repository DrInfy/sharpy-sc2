from typing import List

from sharpy.knowledges import Knowledge
from sharpy.combat import CombatGoal, CombatAction, EnemyData
from .state_step import StateStep
from sc2 import AbilityId


class StateStalker(StateStep):
    def __init__(self, knowledge: Knowledge):
        self.cooldown = 45.1
        super().__init__(knowledge)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        if not enemies.powered_enemies.exists:
            return []

        stalker = goal.unit

        if self.cd_manager.is_ready(stalker.tag, AbilityId.EFFECT_BLINK_STALKER, self.cooldown):
            if enemies.our_power.is_enough_for(enemies.enemy_power, 1.3):
                # We have the advantage, enable offensive blink
                distance = enemies.closest.distance_to(stalker)
                own_range = self.unit_values.real_range(stalker, enemies.closest, self.knowledge)
                enemy_range = self.unit_values.real_range(stalker, enemies.closest, self.knowledge)

                if distance > own_range and own_range < enemy_range and distance < own_range + 5:
                    # Blink to tanks, colossi and tempest
                    self.cd_manager.used_ability(stalker.tag, AbilityId.EFFECT_BLINK_STALKER)
                    target = stalker.position.towards(enemies.closest.position, 8)
                    return [CombatAction(stalker, target, False, AbilityId.EFFECT_BLINK_STALKER)]

            if stalker.shield_percentage < 0.1:
                self.cd_manager.used_ability(stalker.tag, AbilityId.EFFECT_BLINK_STALKER)
                target = stalker.position.towards(enemies.enemy_center, -8)
                return [CombatAction(stalker, target, False, AbilityId.EFFECT_BLINK_STALKER)]

        return []

