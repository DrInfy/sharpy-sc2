from sharpy.managers.combat2 import MicroStep, Action, MoveType, NoAction
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sc2.units import Units


class MicroZealots(MicroStep):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        if self.move_type == MoveType.DefensiveRetreat or self.move_type == MoveType.PanicRetreat:
            return current_command

        if self.engage_ratio > 0.25 and self.closest_group:
            if self.ready_to_attack_ratio > 0.25 or self.closest_group_distance < 2:
                return Action(self.closest_group.center, True)
            return Action(self.closest_group.center.towards(self.center, -3), False)
        #if self.engage_percentage == 0
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if unit.has_buff(BuffId.CHARGING):
            return NoAction()

        ground_units = self.enemies_near_by.not_flying
        if not ground_units:
            current_command.is_attack = False
            return current_command
        # if self.knowledge.enemy_race == Race.Protoss:
        #     if self.engage_percentage < 0.25:
        #         buildings = self.enemies_near_by.sorted_by_distance_to(unit)
        #         if buildings:
        #             if buildings.first.health + buildings.first.shield < 200:
        #                 return Action(buildings.first, True)
        #             pylons = buildings(UnitTypeId.PYLON)
        #             if pylons:
        #                 return Action(buildings.first, True)
        return current_command
