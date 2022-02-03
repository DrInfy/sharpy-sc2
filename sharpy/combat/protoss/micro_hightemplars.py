from typing import List

from sc2.position import Point2

from sc2.ids.effect_id import EffectId
from sc2.units import Units

from sharpy.combat import GenericMicro, Action, CombatUnits
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
from sharpy.interfaces.combat_manager import MoveType


class MicroHighTemplars(GenericMicro):
    def __init__(self):
        super().__init__()
        self.ordered_storms: List[Point2] = []

    def init_group(
        self,
        rules: "MicroRules",
        group: CombatUnits,
        units: Units,
        enemy_groups: List[CombatUnits],
        move_type: MoveType,
        original_target: Point2,
    ):
        super().init_group(rules, group, units, enemy_groups, move_type, original_target)
        self.ordered_storms.clear()

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        if self.cd_manager.is_ready(unit.tag, AbilityId.PSISTORM_PSISTORM):
            stormable_enemies = self.cache.enemy_in_range(unit.position, 10).not_structure
            storms = self.cache.effects(EffectId.PSISTORMPERSISTENT)

            for storm in storms:
                stormable_enemies = stormable_enemies.further_than(3, storm[0])

            for storm in self.ordered_storms:
                stormable_enemies = stormable_enemies.further_than(3, storm)

            if len(stormable_enemies) > 4:
                center = stormable_enemies.center
                target = stormable_enemies.closest_to(center)
                if len(stormable_enemies.closer_than(3, target.position)) > 3:
                    self.ordered_storms.append(target.position)
                    return Action(target.position, False, AbilityId.PSISTORM_PSISTORM)

        if self.cd_manager.is_ready(unit.tag, AbilityId.FEEDBACK_FEEDBACK):
            feedback_enemies = self.cache.enemy_in_range(unit.position, 10).filter(
                lambda u: u.energy > 74 and not u.is_structure
            )
            if feedback_enemies:
                closest = feedback_enemies.closest_to(unit)
                return Action(closest, False, AbilityId.FEEDBACK_FEEDBACK)

        return super().unit_solve_combat(unit, current_command)
