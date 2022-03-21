from typing import Optional

from sc2.ids.ability_id import AbilityId
from sharpy.combat import Action, GenericMicro
from sc2.unit import Unit
from sc2.units import Units


class MicroReaper(GenericMicro):
    def __init__(self):
        super().__init__()
        self.run_percentage = 0.15
        self.grenade_available = 0

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return super().group_solve_combat(units, current_command)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:

        # avoid stepping on grenades
        for effect in self.ai.state.effects:
            if effect.id != "KD8CHARGE":
                continue
            for epos in effect.positions:
                if unit.position.distance_to_point2(epos) < 4:
                    return Action(unit.position.towards(epos, -4), False, AbilityId.MOVE_MOVE)

        # shoot grenades
        grenade_best_score = 0
        grenade_target: Optional[Unit] = None
        enemy: Unit

        for enemy in self.enemies_near_by:
            d = enemy.distance_to(unit)
            if d < 6:
                grenade_score = self.cache.enemy_in_range(enemy.position, 3).not_structure.not_flying.amount

                if grenade_score > grenade_best_score:
                    grenade_target = enemy
                    grenade_best_score = grenade_score

        if (
            grenade_target is not None
            and self.grenade_available < self.ai.time
            and self.cd_manager.is_ready(unit.tag, AbilityId.KD8CHARGE_KD8CHARGE)
        ):
            self.grenade_available = self.ai.time + 1
            return Action(grenade_target.position, False, AbilityId.KD8CHARGE_KD8CHARGE)

        # run away if hurt
        if unit.health_percentage < self.run_percentage:
            return self.stay_safe(unit, current_command)

        return super().unit_solve_combat(unit, current_command)

    def stay_safe(self, unit: Unit, current_command: Action) -> Action:
        """Partial retreat, micro back."""
        pos = self.pather.find_weak_influence_ground(unit.position, 6)
        return Action(pos, False)
