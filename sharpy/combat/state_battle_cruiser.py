from typing import List

from .state_step import StateStep
from sharpy.combat import CombatGoal, CombatAction, EnemyData
from sc2 import AbilityId, UnitTypeId
from sc2.units import Units


class StateBattleCruiser(StateStep):
    def __init__(self, knowledge):
        self.cooldown = 71.1
        super().__init__(knowledge)
        self.knowledge = knowledge

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        return [command]  # Skips all else

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        bc = goal.unit
        if bc.health < 50 and self.cd_manager.is_ready(bc.tag, AbilityId.EFFECT_TACTICALJUMP, self.cooldown):
            zones = self.knowledge.our_zones_with_minerals
            if zones:
                position = zones[0].behind_mineral_position_center
                self.cd_manager.used_ability(bc.tag, AbilityId.EFFECT_TACTICALJUMP)
                return CombatAction(bc, position, False, AbilityId.EFFECT_TACTICALJUMP)

        if not self.cd_manager.is_ready(bc.tag, AbilityId.EFFECT_TACTICALJUMP, self.cooldown) and bc.health_percentage < 0.9:
            scvs: Units = self.knowledge.unit_cache.own(UnitTypeId.SCV)
            if len(scvs) > 0 and scvs.closest_distance_to(bc) < 4:
                # Stay put!
                return CombatAction(bc, bc.position, False)

        return command
