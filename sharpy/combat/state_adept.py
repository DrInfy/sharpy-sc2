from typing import List

import sc2
from sc2.constants import *

from sharpy.combat import CombatGoal, CombatAction, EnemyData
from .state_step import StateStep
from sharpy.knowledges import Knowledge
from sharpy.managers.roles import UnitTask


class StateAdept(StateStep):
    def __init__(self, knowledge: Knowledge):
        super().__init__(knowledge)
        self.tag_shift_used_dict = {}
        self.cooldown = 11.1
        self.knowledge = knowledge

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        if not self.knowledge.known_enemy_units.exists:
            return []

        for adept in self.ai.units(sc2.UnitTypeId.ADEPT).tags_not_in(self.knowledge.roles.roles[UnitTask.Scouting.value].tags):
            if adept.shield_percentage < 0.75:
                if self.tag_shift_used_dict.get(adept.tag, 0) + self.cooldown < self.ai.time:
                    self.tag_shift_used_dict[adept.tag] = self.ai.time
                    target = adept.position.towards(self.knowledge.known_enemy_units.closest_to(adept.position), -10)
                    return [CombatAction(goal.unit, target, False, AbilityId.ADEPTPHASESHIFT_ADEPTPHASESHIFT)]

        return []
