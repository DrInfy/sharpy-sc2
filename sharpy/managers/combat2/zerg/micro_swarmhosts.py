from typing import List

from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
from sc2.units import Units

from sharpy.managers.combat2 import Action, MicroStep, MoveType

HOST_RANGE = 15


class MicroSwarmHosts(MicroStep):
    """Micro Swarm Hosts."""

    def __init__(self, knowledge) -> None:
        """Run setup."""
        super().__init__(knowledge)
        self.last_used_any = 0
        self.tags_ready: List[int] = []

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        """Have all units execute the current command."""
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        """Micro individual units."""
        if self.move_type == MoveType.DefensiveRetreat:
            return current_command

        closest = self.closest_units.get(unit.tag)
        if not closest or closest.distance_to(unit) > HOST_RANGE:
            # not in combat, follow the army
            return current_command

        relevant_enemies = self.cache.enemy_in_range(unit.position, HOST_RANGE)
        if len(relevant_enemies) < 2:
            return self.stay_safe(unit, current_command)

        center = relevant_enemies.center

        if self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_SPAWNLOCUSTS):
            distance = self.pather.walk_distance(unit.position, center)
            if distance < HOST_RANGE:
                return Action(
                    center,
                    False,
                    AbilityId.EFFECT_SPAWNLOCUSTS,
                    debug_comment="Spawning Locusts",
                )
            else:
                return Action(center, False)

        return self.stay_safe(unit, current_command)

    def stay_safe(self, unit: Unit, current_command: Action) -> Action:
        """Partial retreat, micro back."""
        pos = self.pather.find_weak_influence_ground(unit.position, 5)
        return Action(pos, False)
