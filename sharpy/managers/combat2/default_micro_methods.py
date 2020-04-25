from abc import abstractmethod
from typing import List, Optional, Dict, Callable

from sc2 import UnitTypeId, Race, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units
from sharpy.managers.combat2 import CombatUnits, MoveType, MicroStep, Action

changelings = {
    UnitTypeId.CHANGELING,
    UnitTypeId.CHANGELINGMARINE,
    UnitTypeId.CHANGELINGMARINESHIELD,
    UnitTypeId.CHANGELINGZEALOT,
    UnitTypeId.CHANGELINGZERGLING,
    UnitTypeId.CHANGELINGZERGLINGWINGS,
}


class DefaultMicroMethods:
    @staticmethod
    def init_micro_group(
        step: MicroStep, group: CombatUnits, units: Units, enemy_groups: List[CombatUnits], move_type: MoveType
    ):
        ready_to_attack = 0

        step.closest_group = group.closest_target_group(enemy_groups)
        if step.closest_group:
            step.closest_group_distance = group.center.distance_to(step.closest_group.center)
        else:
            step.closest_group_distance = 100000
        step.enemy_groups = enemy_groups
        step.center = units.center
        step.enemies_near_by: Units = step.knowledge.unit_cache.enemy_in_range(step.center, 15 + len(group.units) * 0.1)

        step.engaged_power.add_units(step.enemies_near_by)

        engage_count = 0
        can_engage_count = 0
        step.attack_range = 0
        step.enemy_attack_range = 0
        attack_range_count = 0
        enemy_attack_range_count = 0

        for unit in units:
            closest_distance = 1000
            if step.ready_to_shoot(unit):
                ready_to_attack += 1

            engage_added = False
            can_engage_added = False
            for enemy_near in step.enemies_near_by:  # type: Unit
                d = enemy_near.distance_to(unit)
                if d < closest_distance:
                    step.closest_units[unit.tag] = enemy_near
                    closest_distance = d

                att_range = step.unit_values.real_range(enemy_near, unit)
                step.enemy_attack_range += att_range
                enemy_attack_range_count += 1
                if not engage_added and d < att_range:
                    engage_count += 1
                    engage_added = True

                att_range = step.unit_values.real_range(unit, enemy_near)
                step.attack_range += att_range
                attack_range_count += 1

                if not can_engage_added and d < att_range:
                    can_engage_count += 1
                    can_engage_added = True

        if attack_range_count > 0:
            step.attack_range = step.attack_range / attack_range_count

        if enemy_attack_range_count > 0:
            step.enemy_attack_range = step.enemy_attack_range / enemy_attack_range_count

        step.ready_to_attack_ratio = ready_to_attack / len(units)
        step.engage_ratio = engage_count / len(units)
        step.can_engage_ratio = can_engage_count / len(units)

    @staticmethod
    def focus_fire(
        step: MicroStep, unit: Unit, current_command: Action, prio: Optional[Dict[UnitTypeId, int]]
    ) -> Action:
        shoot_air = step.unit_values.can_shoot_air(unit)
        shoot_ground = step.unit_values.can_shoot_ground(unit)

        air_range = step.unit_values.air_range(unit)
        ground_range = step.unit_values.ground_range(unit)
        lookup = min(air_range + 3, ground_range + 3)
        enemies = step.cache.enemy_in_range(unit.position, lookup)

        last_target = step.last_targeted(unit)

        if not enemies:
            # No enemies to shoot at
            return current_command

        value_func: Callable[[Unit], float]
        if prio:
            value_func = (
                lambda u: 1 if u.type_id in changelings else prio.get(u.type_id, -1) * (1 - u.shield_health_percentage)
            )
        else:
            value_func = (
                lambda u: 1
                if u.type_id in changelings
                else 2 * step.unit_values.power_by_type(u.type_id, 1 - u.shield_health_percentage)
            )

        best_target: Optional[Unit] = None
        best_score: float = 0
        for enemy in enemies:  # type: Unit
            if not step.is_target(enemy):
                continue

            if not shoot_air and enemy.is_flying:
                continue

            if not shoot_ground and not enemy.is_flying:
                continue

            pos: Point2 = enemy.position
            score = value_func(enemy) + (1 - pos.distance_to(unit) / lookup)
            if enemy.tag == last_target:
                score += 3

            if step.focus_fired.get(enemy.tag, 0) > enemy.health:
                score *= 0.1

            if score > best_score:
                best_target = enemy
                best_score = score

        if best_target:
            step.focus_fired[best_target.tag] = (
                step.focus_fired.get(best_target.tag, 0) + unit.calculate_damage_vs_target(best_target)[0]
            )

            return Action(best_target, True)

        return current_command

    @staticmethod
    def melee_focus_fire(
        step: MicroStep, unit: Unit, current_command: Action, prio: Optional[Dict[UnitTypeId, int]]
    ) -> Action:
        ground_range = step.unit_values.ground_range(unit)
        lookup = ground_range + 3
        enemies = step.cache.enemy_in_range(unit.position, lookup)

        last_target = step.last_targeted(unit)

        if not enemies:
            # No enemies to shoot at
            return current_command

        def melee_value(u: Unit):
            val = 1 - u.shield_health_percentage
            range = step.unit_values.real_range(unit, u)
            if unit.distance_to(u) < range:
                val += 2
            if step.knowledge.enemy_race == Race.Terran and unit.is_structure and unit.build_progress < 1:
                # if building isn't finished, focus on the possible scv instead
                val -= 2
            return val

        value_func = melee_value
        close_enemies = step.cache.enemy_in_range(unit.position, lookup)

        best_target: Optional[Unit] = None
        best_score: float = 0

        for enemy in close_enemies:  # type: Unit
            if enemy.is_flying:
                continue

            pos: Point2 = enemy.position
            score = value_func(enemy) + (1 - pos.distance_to(unit) / lookup)
            if enemy.tag == last_target:
                score += 1

            if step.focus_fired.get(enemy.tag, 0) > enemy.health:
                score *= 0.1

            if score > best_score:
                best_target = enemy
                best_score = score

        if best_target:
            step.focus_fired[best_target.tag] = step.focus_fired.get(best_target.tag, 0)
            return Action(best_target, True)

        return current_command

    @staticmethod
    def ready_to_shoot(step: MicroStep, unit: Unit) -> bool:
        delay_to_shoot = step.client.game_step + 1.5

        if unit.type_id == UnitTypeId.CYCLONE:
            if step.cd_manager.is_ready(unit.tag, AbilityId.CANCEL_LOCKON):
                return False

        if unit.type_id == UnitTypeId.DISRUPTOR:
            return step.cd_manager.is_ready(unit.tag, AbilityId.EFFECT_PURIFICATIONNOVA)

        if unit.type_id == UnitTypeId.ORACLE:
            tick = step.ai.state.game_loop % 16
            return tick < 8

        if unit.type_id == UnitTypeId.CARRIER:
            tick = step.ai.state.game_loop % 32
            return tick < 8

        return unit.weapon_cooldown <= delay_to_shoot
