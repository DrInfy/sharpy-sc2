from sharpy.managers.combat2 import GenericMicro, Action
from sc2 import AbilityId
from sc2.unit import Unit


class MicroHighTemplars(GenericMicro):

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        if self.cd_manager.is_ready(unit.tag, AbilityId.PSISTORM_PSISTORM):
            stormable_enemies = self.cache.enemy_in_range(unit.position, 10).not_structure
            if len(stormable_enemies) > 6:
                center = stormable_enemies.center
                target = stormable_enemies.closest_to(center)
                return Action(target.position, False, AbilityId.PSISTORM_PSISTORM)

        if self.cd_manager.is_ready(unit.tag, AbilityId.FEEDBACK_FEEDBACK):
            feedback_enemies = self.cache.enemy_in_range(unit.position, 10) \
                .filter(lambda u: u.energy > 74 and not u.is_structure)
            if feedback_enemies:
                closest = feedback_enemies.closest_to(unit)
                return Action(closest, False, AbilityId.FEEDBACK_FEEDBACK)

        return super().unit_solve_combat(unit, current_command)
