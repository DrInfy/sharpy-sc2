from sharpy.managers.combat2 import GenericMicro, Action
from sc2 import AbilityId, Optional
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit


class MicroRavagers(GenericMicro):
    def __init__(self, knowledge):
        super().__init__(knowledge)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        shuffler = unit.tag % 10

        if not self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_CORROSIVEBILE):
            return super().unit_solve_combat(unit, current_command)

        if self.engaged_power.power > 10:
            best_score = 0
            target: Optional[Unit] = None
            enemy: Unit

            for enemy in self.enemies_near_by:
                d = enemy.distance_to(unit)
                if d < 9:
                    score = d * 0.2 - enemy.movement_speed + enemy.radius + self.unit_values.power(enemy)
                    score += 0.1 * (enemy.tag % (shuffler + 2))

                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                return Action(target.position, False, AbilityId.EFFECT_CORROSIVEBILE)

        return super().unit_solve_combat(unit, current_command)
