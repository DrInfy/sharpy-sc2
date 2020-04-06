from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.units import Units
from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import AbilityId
from sc2.unit import Unit


class MicroVoidrays(MicroStep):
    def should_retreat(self, unit: Unit) -> bool:
        if unit.shield_max + unit.health_max > 0:
            health_percentage = (unit.shield + unit.health) / (unit.shield_max + unit.health_max)
        else:
            health_percentage = 0
        if health_percentage < 0.2 or unit.weapon_cooldown < 0:
            # low hp or unit can't attack
            return True

        for effect in self.ai.state.effects:
            if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                if Point2.center(effect.positions).distance_to(unit) < 3:
                    return True
            if effect.id == EffectId.BLINDINGCLOUDCP:
                if Point2.center(effect.positions).distance_to(unit) < 4:
                    return True
            if effect.id == EffectId.PSISTORMPERSISTENT:
                if Point2.center(effect.positions).distance_to(unit) < 4:
                    return True
        return False

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            return current_command

        if self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT):
            close_enemies = self.cache.enemy_in_range(unit.position, 7).filter(lambda u: u.is_armored)
            if close_enemies:
                return Action(None, False, AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT)

        if not self.should_shoot() and self.should_retreat(unit):
            pos = self.pather.find_weak_influence_air(unit.position, 4)
            return Action(pos, False)

        return self.focus_fire(unit, current_command, None)

    def should_shoot(self):
        tick = self.ai.state.game_loop % 24
        return tick < 8
