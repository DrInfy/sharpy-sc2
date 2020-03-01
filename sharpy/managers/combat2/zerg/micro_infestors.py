from sc2.ids.buff_id import BuffId
from sc2.ids.effect_id import EffectId
from sc2.position import Point2
from sc2.units import Units
from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import AbilityId, UnitTypeId, Optional
from sc2.unit import Unit


class MicroInfestors(MicroStep):

    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.aoe_available = 0

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.engage_ratio < 0.25 and self.can_engage_ratio < 0.25:
            return current_command

        if self.move_type in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            return current_command

        closest = self.closest_units.get(unit.tag)
        if not closest or closest.distance_to(unit) > 14:
            # not in combat, follow the army
            return current_command

        if unit.energy < 75:
            focus = self.group.center
            best_position = self.pather.find_weak_influence_ground(focus, 6)
            return Action(best_position, False)

        if self.cd_manager.is_ready(unit.tag, AbilityId.NEURALPARASITE_NEURALPARASITE):
            shuffler = unit.tag % 10
            best_score = 300
            target: Optional[Unit] = None
            enemy: Unit

            for enemy in self.enemies_near_by:
                d = enemy.distance_to(unit)
                if d < 11 and self.unit_values.power(enemy) > 1 and not enemy.has_buff(BuffId.NEURALPARASITE):
                    score = enemy.health + self.unit_values.power(enemy) * 50
                    # TODO: Needs proper target locking in order to not fire at the same target
                    # Simple and stupid way in an attempt to not use ability on same target:
                    score += (enemy.tag % (shuffler + 2))

                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                return Action(target, False, AbilityId.NEURALPARASITE_NEURALPARASITE)

        if (self.aoe_available < self.ai.time
            and self.cd_manager.is_ready(unit.tag, AbilityId.FUNGALGROWTH_FUNGALGROWTH)
            and self.engaged_power.power > 4
        ):
            best_score = 2
            target: Optional[Unit] = None
            enemy: Unit

            for enemy in self.enemies_near_by:
                d = enemy.distance_to(unit)
                if d < 11 and self.unit_values.power(enemy) > 0.5 and not enemy.has_buff(BuffId.FUNGALGROWTH):
                    score = self.cache.enemy_in_range(enemy.position, 2).amount

                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                self.aoe_available = self.ai.time + 2
                return Action(target.position, False, AbilityId.FUNGALGROWTH_FUNGALGROWTH)

        return self.stay_safe(unit, current_command)

    def stay_safe(self, unit: Unit, current_command: Action) -> Action:
        """Partial retreat, micro back."""
        pos = self.pather.find_weak_influence_ground(unit.position, 5)
        return Action(pos, False)
