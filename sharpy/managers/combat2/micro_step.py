from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Any, Callable, Union, TYPE_CHECKING

import sc2
from sharpy.general.extended_power import ExtendedPower
from sharpy.managers.combat2.move_type import MoveType
from sc2.ids.buff_id import BuffId
from .action import Action
from .combat_units import CombatUnits

from sc2 import AbilityId, UnitTypeId, Race
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

if TYPE_CHECKING:
    from sharpy.managers import *

changelings = {
    UnitTypeId.CHANGELING,
    UnitTypeId.CHANGELINGMARINE,
    UnitTypeId.CHANGELINGMARINESHIELD,
    UnitTypeId.CHANGELINGZEALOT,
    UnitTypeId.CHANGELINGZERGLING,
    UnitTypeId.CHANGELINGZERGLINGWINGS,
}

class MicroStep(ABC):
    def __init__(self, knowledge):
        self.knowledge: 'Knowledge' = knowledge
        self.ai: sc2.BotAI = knowledge.ai
        self.unit_values: UnitValue = knowledge.unit_values
        self.cd_manager: CooldownManager = knowledge.cooldown_manager
        self.pather: PathingManager = knowledge.pathing_manager
        self.cache: UnitCacheManager = knowledge.unit_cache
        self.delay_to_shoot = self.ai._client.game_step + 1.5
        self.enemy_groups: List[CombatUnits] = []
        self.ready_to_attack_ratio: float = 0.0
        self.center: Point2 = Point2((0, 0))
        self.group: CombatUnits
        self.engage_ratio = 0
        self.can_engage_ratio = 0
        self.closest_group: CombatUnits
        self.engaged: Dict[int, List[int]] = dict()
        self.engaged_power = ExtendedPower(knowledge.unit_values)
        self.our_power = ExtendedPower(knowledge.unit_values)
        self.closest_units: Dict[int, Optional[Unit]] = dict()
        self.move_type = MoveType.Assault
        self.attack_range = 0
        self.enemy_attack_range = 0

        self.focus_fired: Dict[int, float] = dict()


    def init_group(self, group: CombatUnits, units: Units, enemy_groups: List[CombatUnits], move_type: MoveType):
        self.focus_fired.clear()
        self.group = group
        self.move_type = move_type
        ready_to_attack = 0

        self.our_power = group.power
        self.closest_units.clear()
        self.engaged_power.clear()

        self.closest_group = group.closest_target_group(enemy_groups)
        if self.closest_group:
            self.closest_group_distance = group.center.distance_to(self.closest_group.center)
        else:
            self.closest_group_distance = 100000
        self.enemy_groups = enemy_groups
        self.center = units.center
        self.enemies_near_by: Units = self.knowledge.unit_cache.enemy_in_range(self.center, 15 + len(group.units) * 0.1)

        self.engaged_power.add_units(self.enemies_near_by)

        engage_count = 0
        can_engage_count = 0
        self.attack_range = 0
        self.enemy_attack_range = 0
        attack_range_count = 0
        enemy_attack_range_count = 0

        for unit in units:
            closest_distance = 1000
            if self.ready_to_shoot(unit):
                ready_to_attack += 1

            engage_added = False
            can_engage_added = False
            for enemy_near in self.enemies_near_by:  # type: Unit
                d = enemy_near.distance_to(unit)
                if d < closest_distance:
                    self.closest_units[unit.tag] = enemy_near
                    closest_distance = d

                att_range = self.unit_values.real_range(enemy_near, unit)
                self.enemy_attack_range += att_range
                enemy_attack_range_count += 1
                if not engage_added and d < att_range:
                    engage_count += 1
                    engage_added = True

                att_range = self.unit_values.real_range(unit, enemy_near)
                self.attack_range += att_range
                attack_range_count += 1

                if not can_engage_added and d < att_range:
                    can_engage_count += 1
                    can_engage_added = True

        if attack_range_count > 0:
            self.attack_range = self.attack_range / attack_range_count

        if enemy_attack_range_count > 0:
            self.enemy_attack_range = self.enemy_attack_range / enemy_attack_range_count

        self.ready_to_attack_ratio = ready_to_attack / len(units)
        self.engage_ratio = engage_count / len(units)
        self.can_engage_ratio = can_engage_count / len(units)

    def ready_to_shoot(self, unit: Unit) -> bool:
        if unit.type_id == UnitTypeId.CYCLONE:
            # if knowledge.cooldown_manager.is_ready(self.unit.tag, AbilityId.LOCKON_LOCKON):
            #     self.ready_to_shoot = True
            #     return
            if self.cd_manager.is_ready(unit.tag, AbilityId.CANCEL_LOCKON):
                return False


        if unit.type_id == UnitTypeId.DISRUPTOR:
            return self.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_PURIFICATIONNOVA)

        if unit.type_id == UnitTypeId.ORACLE:
            tick = self.ai.state.game_loop % 16
            return tick < 8

        if unit.type_id == UnitTypeId.CARRIER:
            tick = self.ai.state.game_loop % 32
            return tick < 8

        return unit.weapon_cooldown <= self.delay_to_shoot

    @abstractmethod
    def group_solve_combat(self, units: Units, current_command: Action) -> Action:
        pass

    @abstractmethod
    def unit_solve_combat(self, unit: Unit, current_command: Action) -> Action:
        pass


    def focus_fire(self, unit: Unit, current_command: Action, prio: Optional[Dict[UnitTypeId, int]]) -> Action:
        shoot_air = self.unit_values.can_shoot_air(unit)
        shoot_ground = self.unit_values.can_shoot_ground(unit)

        air_range = self.unit_values.air_range(unit)
        ground_range = self.unit_values.ground_range(unit)
        lookup = min(air_range + 3, ground_range + 3)
        enemies = self.cache.enemy_in_range(unit.position, lookup)

        last_target = self.last_targeted(unit)

        if not enemies:
            # No enemies to shoot at
            return current_command

        value_func: Callable[[Unit],  float]
        if prio:
            value_func = lambda u: 1 if u.type_id in changelings else prio.get(u.type_id, -1) \
                  * (1 - u.shield_health_percentage)
        else:
            value_func = lambda u: 1 if u.type_id in changelings else 2 \
                  * self.unit_values.power_by_type(u.type_id, 1 - u.shield_health_percentage)

        best_target: Optional[Unit] = None
        best_score: float = 0
        for enemy in enemies:  # type: Unit
            if not self.is_target(enemy):
                continue

            if not shoot_air and enemy.is_flying:
                continue

            if not shoot_ground and not enemy.is_flying:
                continue

            pos: Point2 = enemy.position
            score = value_func(enemy) + (1 - pos.distance_to(unit) / lookup)
            if enemy.tag == last_target:
                score += 3

            if self.focus_fired.get(enemy.tag, 0) > enemy.health:
                score *= 0.1

            if score > best_score:
                best_target = enemy
                best_score = score

        if best_target:
            self.focus_fired[best_target.tag] = self.focus_fired.get(best_target.tag, 0) + \
                                                unit.calculate_damage_vs_target(best_target)[0]

            return Action(best_target, True)

        return current_command

    def melee_focus_fire(self, unit: Unit, current_command: Action) -> Action:
        ground_range = self.unit_values.ground_range(unit)
        lookup = ground_range + 3
        enemies = self.cache.enemy_in_range(unit.position, lookup)

        last_target = self.last_targeted(unit)

        if not enemies:
            # No enemies to shoot at
            return current_command

        def melee_value(u: Unit):
            val = 1 - u.shield_health_percentage
            range = self.unit_values.real_range(unit, u)
            if unit.distance_to(u) < range:
                val += 2
            if self.knowledge.enemy_race == Race.Terran and unit.is_structure and unit.build_progress < 1:
                # if building isn't finished, focus on the possible scv instead
                val -= 2
            return val

        value_func = melee_value
        close_enemies = self.cache.enemy_in_range(unit.position, lookup)

        best_target: Optional[Unit] = None
        best_score: float = 0

        for enemy in close_enemies:  # type: Unit
            if enemy.is_flying:
                continue

            pos: Point2 = enemy.position
            score = value_func(enemy) + (1 - pos.distance_to(unit) / lookup)
            if enemy.tag == last_target:
                score += 1

            if self.focus_fired.get(enemy.tag, 0) > enemy.health:
                score *= 0.1

            if score > best_score:
                best_target = enemy
                best_score = score

        if best_target:
            self.focus_fired[best_target.tag] = self.focus_fired.get(best_target.tag, 0)
            return Action(best_target, True)

        return current_command

    def last_targeted(self, unit: Unit) -> Optional[int]:
        if unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action = unit.orders[0]
            # targeting unit
            if isinstance(current_action.target, int):
                # tag found
                return current_action.target
        return None

    def is_locked_on(self, unit: Unit) -> bool:
        if unit.has_buff(BuffId.LOCKON):
            return True
        return False

    def is_target(self, unit: Unit) -> bool:
        return not unit.is_memory and unit.can_be_attacked and not unit.is_hallucination and not unit.is_snapshot
