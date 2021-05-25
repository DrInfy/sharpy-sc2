from sharpy.combat import Action, GenericMicro
from sc2.unit import Unit
from sc2.units import Units
from sharpy.interfaces.combat_manager import MoveType, retreat_move_types, retreat_or_push_move_types
from sharpy.managers.core import UnitValue


class MicroZerglings(GenericMicro):
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:

        if self.move_type in retreat_or_push_move_types:
            return current_command

        if self.engage_ratio > 0.5 and self.closest_group:
            if self.ready_to_attack_ratio > 0.8 or self.closest_group_distance < 2:
                return Action(self.closest_group.center, True)
            if self.ready_to_attack_ratio < 0.25:
                return Action(self.closest_group.center, True)
            return Action(self.closest_group.center.towards(self.center, -3), False)
        # if self.engage_percentage == 0
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

        if self.move_type in retreat_move_types:
            return current_command

        if self.move_type == MoveType.Push and unit.distance_to(current_command.target) > 3:
            # MoveType.Push and we didn't reach the target
            if self.ready_to_shoot(unit):
                # focus_fire takes care of not attacking things behind us
                focus_action = self.melee_focus_fire(unit, current_command, self.prio_dict)
                if isinstance(focus_action.target, Unit):
                    return focus_action

            # If not ready to attack, or focus_fire() didn't find a target, move command forward.
            position = self.pather.find_influence_ground_path(unit.position, current_command.target, 4)
            return Action(position, False)

        # u: Unit
        enemies = self.cache.enemy_in_range(unit.position, unit.radius + unit.ground_range + 1).filter(
            lambda u: not u.is_flying and u.type_id not in self.unit_values.combat_ignore
        )
        if enemies:
            current_command = Action(enemies.center, True)
            return self.melee_focus_fire(unit, current_command, self.prio_dict)
        return current_command
