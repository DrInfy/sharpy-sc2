from sc2 import UnitTypeId
from sc2.position import Point2
from sharpy.managers.combat2 import Action, MicroStep
from sc2.unit import Unit
from sc2.units import Units


class MicroObservers(MicroStep):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if isinstance(current_command.target, Unit):
            target_pos = current_command.target.position
        else:
            target_pos = current_command.target

        target = self.pather.find_path(self.group.center, target_pos, 8) # move ahead of group
        enemies = self.cache.enemy_in_range(target, 12, False)
        other_observers = self.cache.own(UnitTypeId.OBSERVER).tags_not_in([unit.tag])
        if other_observers:
            # Try to keep observers separated from each other
            closest = other_observers.closest_to(unit)
            if closest.distance_to(unit) < 5:
                pos: Point2 = closest.position
                target = unit.position.towards(pos, -6)

        # for enemy in enemies:  # type: Unit
        #     if enemy.detect_range > 0 and enemy.detect_range > target.distance_to(enemy):
        #         break
        if enemies:
            target = self.pather.find_weak_influence_air(target, 10)

        return Action(target, False)


