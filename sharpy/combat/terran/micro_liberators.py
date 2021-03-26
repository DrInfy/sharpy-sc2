from typing import Dict

from sc2.units import Units
from sharpy.combat import Action, MoveType, MicroStep
from sc2 import UnitTypeId, AbilityId, Optional
from sc2.unit import Unit
from sc2.position import Point2


class MicroLiberators(MicroStep):
    def __init__(self, group_distance: float = -5):
        super().__init__()
        self.last_siege = 0
        self.group_distance = group_distance
        self.focus_fired: Dict[int, float] = dict()
        self.closest_units: Dict[int, Optional[Unit]] = dict()
        self.lib_count = 0

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        self.lib_count = len(units)
        return super().group_solve_combat(units, current_command)

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        return self.final_solve(unit, super().unit_solve_combat(unit, current_command))

    def final_solve(self, unit: Unit, command: Action) -> Action:
        time = self.knowledge.ai.time
        # TODO: When in AG mode, look for relevant enemies inside the sieged zone.
        my_lib_zone = self.cd_manager.get_liberation_zone(unit.tag)

        if unit.type_id == UnitTypeId.LIBERATORAG and my_lib_zone is not None:
            relevant_ground_enemies = self.cache.enemy_in_range(my_lib_zone, 6.5).not_structure.not_flying.visible
        else:
            relevant_ground_enemies = self.cache.enemy_in_range(unit.position, 11).not_structure.not_flying.visible

        if self.move_type == MoveType.PanicRetreat:
            # TODO: Unsiege
            return command

        if (
            (
                self.move_type == MoveType.Assault
                or self.move_type == MoveType.SearchAndDestroy
                or self.move_type == MoveType.DefensiveRetreat
            )
            and self.engage_ratio < 0.5
            and self.can_engage_ratio < 0.5
            and len(self.closest_units) < 1
        ):
            if self.group.ground_units and isinstance(command.target, Point2):
                # TODO: Unsiege
                # Regroup with the ground army
                return Action(self.group.center.towards(command.target, self.group_distance), False)

        if not relevant_ground_enemies.exists:
            if unit.type_id == UnitTypeId.LIBERATOR:
                return command

            if unit.type_id == UnitTypeId.LIBERATORAG:
                return Action(None, False, AbilityId.MORPH_LIBERATORAAMODE)

        if unit.type_id == UnitTypeId.LIBERATOR and relevant_ground_enemies.exists:
            return self.do_siege(command, relevant_ground_enemies, time, unit)

        return command

    def do_siege(self, command: Action, relevant_ground_enemies: Units, time, unit: Unit):
        # Liberator sieges should spread around the center of our battle group.
        # center = self.group.center
        shuffler = unit.tag % 10
        distance_increaser = 0
        if self.lib_count < 3:
            distance_increaser = 3
        else:
            shuffler = 0.4 * (unit.tag % 10)

        best_score = 0
        target: Optional[Unit] = None
        best_distance: Optional[float] = None
        enemy: Unit

        for enemy in relevant_ground_enemies:
            d = enemy.distance_to(unit)

            if d < 12:
                score = d * 0.2
                score += 0.1 * (enemy.tag % (shuffler + 2))

                if score > best_score:
                    target = enemy
                    best_score = score
                    best_distance = d

        if target is not None:
            self.last_siege = time
            if best_distance > 10:
                self.cd_manager.set_liberation_zone(
                    unit.tag, target.position.towards(unit.position, distance_increaser)
                )
            else:
                self.cd_manager.set_liberation_zone(unit.tag, target.position)
            return Action(target.position, False, AbilityId.MORPH_LIBERATORAGMODE)
        return command
