from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sharpy.combat import Action, GenericMicro, MoveType


class MicroMines(GenericMicro):
    def __init__(self):
        super().__init__()
        self.unburrow_distance = 14
        self.burrow_distance = 10
        self.requested_mode = AbilityId.BURROWUP_WIDOWMINE
        self.closest_enemy = 100

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        relevant_enemies = self.enemies_near_by.visible
        # unburrow if retreating
        if self.move_type == MoveType.PanicRetreat:
            if unit.type_id == UnitTypeId.WIDOWMINEBURROWED and not relevant_enemies.exists:
                self.requested_mode = AbilityId.BURROWUP_WIDOWMINE
        # getting distance to closest enemy
        else:
            if relevant_enemies.exists:
                self.closest_enemy = relevant_enemies.closest_distance_to(unit)
            else:
                self.closest_enemy = 100
        # toggle mode request
        if self.closest_enemy <= self.burrow_distance:
            if self.requested_mode == AbilityId.BURROWUP_WIDOWMINE:
                self.requested_mode = AbilityId.BURROWDOWN_WIDOWMINE

        elif self.closest_enemy >= self.unburrow_distance:
            if self.requested_mode == AbilityId.BURROWDOWN_WIDOWMINE:
                self.requested_mode = AbilityId.BURROWUP_WIDOWMINE

        if unit.type_id == UnitTypeId.WIDOWMINEBURROWED and self.requested_mode == AbilityId.BURROWUP_WIDOWMINE:
            return Action(None, False, self.requested_mode)
        elif unit.type_id == UnitTypeId.WIDOWMINE and self.requested_mode == AbilityId.BURROWDOWN_WIDOWMINE:
            return Action(None, False, self.requested_mode)
        else:
            return current_command
