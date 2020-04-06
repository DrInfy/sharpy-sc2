from sharpy.managers.combat2 import GenericMicro, Action
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit


class MicroVikings(GenericMicro):

    def __init__(self, knowledge):
        super().__init__(knowledge)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        return self.final_solve(unit, super().unit_solve_combat(unit, current_command))

    def final_solve(self, unit: Unit, command: Action) -> Action:
        is_fighter = unit.type_id == UnitTypeId.VIKINGFIGHTER
        if not self.enemies_near_by:
            if is_fighter:
                return command
            else:
                return Action(None, False, AbilityId.MORPH_VIKINGFIGHTERMODE)

        if is_fighter:
            if (not self.enemies_near_by(UnitTypeId.COLOSSUS).exists
                    and not self.enemies_near_by.flying.exists
                    and self.enemies_near_by.not_flying.exists):
                return Action(None, False, AbilityId.MORPH_VIKINGASSAULTMODE)
        else:
            if self.engaged_power.air_presence > 0 or self.enemies_near_by(UnitTypeId.COLOSSUS).exists:
                return Action(None, False, AbilityId.MORPH_VIKINGFIGHTERMODE)

        return command
