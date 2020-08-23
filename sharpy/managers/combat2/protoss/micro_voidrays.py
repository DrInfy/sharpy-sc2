from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.units import Units
from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import AbilityId
from sc2.unit import Unit

# voidrays don't have weapons in the current api
cd_ticks = 22.4 * 0.36
# We'll use a % of the cooldown to shoot and hope that'll be enough
ticks_to_shoot = 6  # cd_ticks * 0.6


class MicroVoidrays(MicroStep):
    def should_retreat(self, unit: Unit) -> bool:
        if unit.shield_max + unit.health_max > 0:
            health_percentage = (unit.shield + unit.health) / (unit.shield_max + unit.health_max)
        else:
            health_percentage = 0
        if health_percentage < 0.2:  # or unit.weapon_cooldown < 0:
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

        shoot = self.should_shoot(unit)
        if not shoot:
            if self.should_retreat(unit):
                pos = self.pather.find_weak_influence_air(unit.position, 4)
                return Action(pos, False)

        current_command = self.focus_fire(unit, current_command, None)

        # if not shoot:
        #     if self.engaged_power.air_power < 1:
        #         if unit.distance_to(current_command.target) > 2:
        #             return Action(current_command.target.position, False)
        return current_command

    def should_shoot(self, unit: Unit):
        if unit.weapon_cooldown < 0:
            tick = self.ai.state.game_loop % cd_ticks
            return tick < ticks_to_shoot
        else:
            return self.ready_to_shoot(unit)
