from sharpy.managers.combat2 import MicroStep, Action, MoveType
from sc2 import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units


class MicroOracles(MicroStep):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if isinstance(current_command.target, Unit):
            target_pos = current_command.target.position
        else:
            target_pos = current_command.target

        if self.move_type == MoveType.PanicRetreat or self.move_type == MoveType.DefensiveRetreat:
            if unit.has_buff(BuffId.ORACLEWEAPON):
                return Action(None, False, AbilityId.BEHAVIOR_PULSARBEAMOFF)
            target = self.pather.find_influence_air_path(unit.position, target_pos)
            return Action(target, False)

        if self.move_type == MoveType.Harass:
            targets = self.cache.enemy(self.knowledge.enemy_worker_type)
            if targets:
                close_to_me = targets.closer_than(8, unit.position)
                close_to_target = targets.closer_than(10, target_pos)
                if close_to_me:
                    targets = close_to_me
                elif close_to_target:
                    targets = close_to_target
        else:
            targets = self.cache.enemy_in_range(unit.position, 10).filter(lambda u: u.is_light and not u.is_flying)

        if targets:
            closest = targets.closest_to(unit)
            distance = closest.distance_to(unit)

            if distance > 40 and unit.has_buff(BuffId.ORACLEWEAPON):
                return Action(None, False, AbilityId.BEHAVIOR_PULSARBEAMOFF)
            if distance < 5:
                if not unit.has_buff(BuffId.ORACLEWEAPON):
                    if unit.energy > 40:
                        return Action(None, False, AbilityId.BEHAVIOR_PULSARBEAMON)
                    else:
                        target = self.pather.find_weak_influence_air(unit.position, 10)
                        return Action(target, False)
                else:
                    return Action(closest, True)

            target = self.pather.find_weak_influence_air(closest.position, 10)
            target = self.pather.find_influence_air_path(unit.position, target)
            return Action(target, False)
        else:
            if unit.has_buff(BuffId.ORACLEWEAPON):
                return Action(None, False, AbilityId.BEHAVIOR_PULSARBEAMOFF)

        target = self.pather.find_influence_air_path(unit.position, target_pos)
        return Action(target, False)
