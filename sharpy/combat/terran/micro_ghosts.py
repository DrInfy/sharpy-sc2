from typing import *

from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sc2.units import Units
from sharpy.combat import *
from sc2.ids.ability_id import AbilityId
from sc2.unit import Unit
from sharpy.interfaces.combat_manager import MoveType


class MicroGhosts(GenericMicro):
    def __init__(self):
        super().__init__()
        self.snipes = {}
        self.emp_available = 0

    def init_group(
        self,
        rules: "MicroRules",
        group: CombatUnits,
        units: Units,
        enemy_groups: List[CombatUnits],
        move_type: MoveType,
        original_target: Point2,
    ):
        super().init_group(
            rules, group, units, enemy_groups, move_type, original_target
        )

    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        return current_command

    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        # There no reason to cloak if near only structures
        enemy_units = self.cache.enemy_in_range(unit.position, 10).filter(lambda u: not u.is_structure and not u.type_id == UnitTypeId.LARVA)
        if unit.energy > 120 and len(enemy_units) > 0 and self.our_power.power < 3:
            return Action(None, False, AbilityId.BEHAVIOR_CLOAKON_GHOST)

        if unit.energy < 50 and len(enemy_units) == 0 and self.our_power.power > 3:
            return Action(None, False, AbilityId.BEHAVIOR_CLOAKOFF_GHOST)

        if self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_GHOSTSNIPE):
            snipe_enemies = self.cache.enemy_in_range(unit.position, 10).filter(
                lambda u: u.is_biological and not u.is_structure and (u.is_armored or u.shield > 0 or u.type_id == UnitTypeId.HELLIONTANK)
            )
            if snipe_enemies:
                best_target = snipe_enemies.closest_to(unit)
                snipe_count = self.snipes.get(best_target.tag, 0)
                if best_target.health > snipe_count * 170:
                    self.snipes[best_target.tag] = snipe_count + 1
                    return Action(best_target, False, AbilityId.EFFECT_GHOSTSNIPE)
                else:
                    return current_command

        if (
            self.emp_available < self.ai.time
            and self.cd_manager.is_ready(unit.tag, AbilityId.EMP_EMP)
            and self.engaged_power.power > 4
        ):
            best_score = 2
            target: Optional[Unit] = None
            enemy: Unit

            for enemy in self.enemies_near_by:
                d = enemy.distance_to(unit)
                if (
                    d < 11
                    and self.unit_values.power(enemy) > 0.5
                    and not enemy.has_buff(BuffId.EMPDECLOAK)
                    and (enemy.energy > 50 or enemy.shield > 50)
                ):
                    score = self.cache.enemy_in_range(enemy.position, 2).filter(
                        lambda u: (u.shield > 0 or u.energy > 0) and not u.is_structure
                    ).amount
                    if score > best_score:
                        target = enemy
                        best_score = score

            if target is not None:
                self.emp_available = self.ai.time + 2
                return Action(target.position, False, AbilityId.EMP_EMP)

        return super().unit_solve_combat(unit, current_command)
