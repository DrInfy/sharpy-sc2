from sharpy.managers.combat2 import Action, MicroStep
from sc2.unit import Unit
from sc2.units import Units


class MicroZerglings(MicroStep):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        if self.engage_ratio > 0.5 and self.closest_group:
            if self.ready_to_attack_ratio > 0.8 or self.closest_group_distance < 2:
                return Action(self.closest_group.center, True)
            if self.ready_to_attack_ratio < 0.25:
                return Action(self.closest_group.center, True)
            return Action(self.closest_group.center.towards(self.center, -3), False)
        #if self.engage_percentage == 0
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
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


