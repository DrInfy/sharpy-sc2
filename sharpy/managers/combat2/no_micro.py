from sharpy.managers.combat2 import MicroStep, Action
from sc2.unit import Unit
from sc2.units import Units


class NoMicro(MicroStep):

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        return current_command
