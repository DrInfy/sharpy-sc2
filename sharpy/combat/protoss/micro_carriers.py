from sc2.position import Point2
from sc2.unit import Unit
from sharpy.combat import GenericMicro, Action
from sharpy.interfaces.combat_manager import MoveType


class MicroCarriers(GenericMicro):
    def __init__(self):
        super().__init__()

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.move_type == MoveType.PanicRetreat:
            return Action(current_command.position, False)

        if self.move_type == MoveType.DefensiveRetreat:
            return Action(current_command.position, self.ready_to_shoot(unit))

        if self.should_retreat(unit) and self.closest_group and not self.ready_to_shoot(unit):
            backstep: Point2 = unit.position.towards(self.closest_group.center, -3)
            backstep = self.pather.find_weak_influence_air(backstep, 5)
            return Action(backstep, False)

        if self.ready_to_shoot(unit):
            if self.closest_group:
                current_command = Action(self.closest_group.center, True)
            else:
                current_command = Action(current_command.target, True)
        elif self.closest_units.get(unit.tag):
            closest = self.closest_units[unit.tag]
            range = 8
            best_position = self.pather.find_low_inside_air(unit.position, closest.position, range)
            return Action(best_position, False)

        return Action(current_command.position, True)
