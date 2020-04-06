from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.units import Units
from sharpy.managers.combat2 import Action, MoveType, GenericMicro
from sc2 import AbilityId, UnitTypeId, Optional
from sc2.unit import Unit


class MicroBattleCruisers(GenericMicro):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        bc = unit

        if bc.health < 50 and self.cd_manager.is_ready(bc.tag, AbilityId.EFFECT_TACTICALJUMP):
            zones = self.knowledge.our_zones_with_minerals
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
                    score += (enemy.tag % (shuffler + 2))

                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                return Action(target, False, AbilityId.YAMATO_YAMATOGUN)

        return super().unit_solve_combat(unit, current_command)

    def should_shoot(self):
        tick = self.ai.state.game_loop % 24
        return tick < 8
