from typing import Dict, Optional

from sc2.ids.ability_id import AbilityId
from sharpy.combat import Action, MoveType, MicroStep
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.position import Point2


class MicroLiberators(MicroStep):
    def __init__(self, group_distance: float = -5):
        super().__init__()
        self.last_siege = 0
        self.group_distance = group_distance
        self.focus_fired: Dict[int, float] = dict()
        self.closest_units: Dict[int, Optional[Unit]] = dict()

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        return self.final_solve(unit, super().unit_solve_combat(unit, current_command))

    def final_solve(self, unit: Unit, command: Action) -> Action:
        time = self.knowledge.ai.time
        # TODO: When in AG mode, look for relevant enemies inside the sieged zone.
        relevant_ground_enemies = self.cache.enemy_in_range(unit.position, 10).not_structure.not_flying.visible

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
            target: Optional[Unit] = None
            enemy: Unit

            for enemy in relevant_ground_enemies:
                if enemy.distance_to(unit) < 12:
                    target = enemy

            if target is not None:
                self.last_siege = time
                # TODO: Save position and zone link with current liberator to CooldownManager
                return Action(target.position, False, AbilityId.MORPH_LIBERATORAGMODE)

        return command
