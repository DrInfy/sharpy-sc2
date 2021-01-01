from sharpy.combat import MicroStep, Action, MoveType, NoAction
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
        # if self.engage_percentage == 0
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if unit.has_buff(BuffId.CHARGING):
            return NoAction()

        ground_units = self.enemies_near_by.not_flying

        if self.move_type not in {MoveType.PanicRetreat, MoveType.DefensiveRetreat}:
            # u: Unit
            enemies = self.cache.enemy_in_range(unit.position, unit.radius + unit.ground_range + 1).filter(
                lambda u: not u.is_flying and u.type_id not in self.unit_values.combat_ignore
            )
            if enemies:
                current_command = Action(enemies.center, True)
                return self.melee_focus_fire(unit, current_command)

        if not ground_units and self.enemies_near_by:
            # Zealots can't attack anything here, go attack move to original destination instead
            return Action(self.original_target, True)
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
