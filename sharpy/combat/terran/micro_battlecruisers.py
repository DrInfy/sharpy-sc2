from typing import Optional

from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.units import Units
from sharpy.combat import Action, GenericMicro
from sc2.unit import Unit


class MicroBattleCruisers(GenericMicro):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        bc = unit
        health_to_jump = 50
        if self.engaged_power.air_power > 8:
            health_to_jump = 100

        if bc.health < health_to_jump and self.cd_manager.is_ready(bc.tag, AbilityId.EFFECT_TACTICALJUMP):
            zones = self.zone_manager.our_zones_with_minerals
            if zones:
                position = zones[0].behind_mineral_position_center
                self.cd_manager.used_ability(bc.tag, AbilityId.EFFECT_TACTICALJUMP)
                return Action(position, False, AbilityId.EFFECT_TACTICALJUMP)

        if not self.cd_manager.is_ready(bc.tag, AbilityId.EFFECT_TACTICALJUMP) and bc.health_percentage < 0.9:
            scvs: Units = self.knowledge.unit_cache.own(UnitTypeId.SCV)
            if len(scvs) > 0 and scvs.closest_distance_to(bc) < 4:
                # Stay put!
                return Action(bc.position, False)

        if self.cd_manager.is_ready(bc.tag, AbilityId.YAMATO_YAMATOGUN):
            shuffler = unit.tag % 10
            best_score = 100  # Let's not waste yamato on marines or zerglings
            target: Optional[Unit] = None
            enemy: Unit

            for enemy in self.enemies_near_by:
                d = enemy.distance_to(unit)
                if d < 11 and self.unit_values.power(enemy) > 1:
                    score = enemy.health
                    # TODO: Needs proper target locking in order to not fire at the same target
                    # Simple and stupid way in an attempt to not use yamato gun on same target:
                    score += enemy.tag % (shuffler + 2)

                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                return Action(target, False, AbilityId.YAMATO_YAMATOGUN)

        return super().unit_solve_combat(unit, current_command)

    def should_shoot(self):
        tick = self.ai.state.game_loop % 24
        return tick < 8
