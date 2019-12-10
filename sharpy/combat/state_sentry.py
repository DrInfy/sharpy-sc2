from typing import List, Dict, Optional

from sc2.ids.buff_id import BuffId

import sc2
from sharpy.general.unit_value import UnitValue
from sc2 import AbilityId, UnitTypeId, Race
from sc2.position import Point2
from sc2.unit import Unit, UnitOrder

from sharpy.knowledges import Knowledge
from .combat_action import CombatAction
from .combat_goal import CombatGoal
from .enemy_data import EnemyData
from .state_step import StateStep


GUARDIAN_SHIELD_RANGE = 4.5
GUARDIAN_SHIELD_TRIGGER_RANGE = 8

FORCE_FIELD_ENERGY_COST = 50
SHIELD_ENERGY_COST = 75
HALLUCINATION_ENERGY_COST = 75


class StateSentry(StateStep):
    """Sentry micro for combat manager"""
    def __init__(self, knowledge):
        super().__init__(knowledge)
        self.shield_cooldown = 11
        self.force_field_cooldown = 10.5
        self.knowledge:Knowledge = knowledge

        self.ai: sc2.BotAI = knowledge.ai
        ramp_ff_movement = 2
        if knowledge.enemy_race == Race.Zerg:
            ramp_ff_movement = 3  # FF higher up so our units can shoot them better
        else:
            ramp_ff_movement = 2

        self.main_ramp_position: Point2 = self.knowledge.base_ramp.bottom_center.towards(
            self.knowledge.base_ramp.top_center, ramp_ff_movement)
        self.main_ramp_position: Point2 = self.main_ramp_position.offset((0.5, -0.5))
        self.tag_shield_used_dict: Dict[int, float] = dict()
        self.ramp_field_used: float = 0
        self.last_hallu_time = 0
        self.last_force_field_time = 0
        self.last_force_field_positions: List[Point2] = []
        self.last_force_fields_used: int = 0
        self.hallu_timer = 4

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        sentry = goal.unit
        time = self.knowledge.ai.time

        if goal.unit.orders and goal.unit.orders[0].ability.id == AbilityId.FORCEFIELD_FORCEFIELD:
            return [CombatAction(sentry, Point2.from_proto(goal.unit.orders[0].target), False, ability=AbilityId.FORCEFIELD_FORCEFIELD)]

        if sentry.energy < FORCE_FIELD_ENERGY_COST:
            return [] # do nothing

        if self.knowledge.expansion_zones[1].is_ours and self.knowledge.expansion_zones[1].is_under_attack:
            # TODO: Should we force field here?
            ...
        else:

            not_flying = enemies.close_enemies.filter(lambda u: not u.is_flying and not u.is_structure)
            if not_flying:
                closest_to_ramp = not_flying.closest_to(self.main_ramp_position)
                closest_to_ramp_distance = closest_to_ramp.distance_to(self.main_ramp_position)
                if closest_to_ramp_distance < 7 \
                        and self.ai.get_terrain_height(sentry) > self.ai.get_terrain_height(closest_to_ramp)\
                        and sentry.distance_to(self.main_ramp_position) < 9:

                    if self.ramp_field_used + self.force_field_cooldown < time:
                        if closest_to_ramp_distance < 2:
                            self.ramp_field_used = time
                            return [CombatAction(sentry, self.main_ramp_position, False, ability= AbilityId.FORCEFIELD_FORCEFIELD)]

                    return []


        if self.last_hallu_time + self.hallu_timer < time and sentry.energy >= HALLUCINATION_ENERGY_COST and enemies.close_enemies.exists:
            hallu_type: Optional[AbilityId] = None

            if self.knowledge.enemy_race == Race.Terran:
                if enemies.close_enemies.of_type([UnitTypeId.BANSHEE, UnitTypeId.BATTLECRUISER]):
                    hallu_type = AbilityId.HALLUCINATION_STALKER
                elif enemies.close_enemies.of_type([UnitTypeId.VIKINGFIGHTER, UnitTypeId.RAVEN]):
                    hallu_type = AbilityId.HALLUCINATION_COLOSSUS
                elif sentry.health + sentry.shield < 30:
                    hallu_type = AbilityId.HALLUCINATION_IMMORTAL
            elif self.knowledge.enemy_race == Race.Zerg:
                if enemies.close_enemies(UnitTypeId.HYDRALISK):
                    hallu_type = AbilityId.HALLUCINATION_VOIDRAY
                if enemies.close_enemies(UnitTypeId.ROACH) or sentry.health + sentry.shield < 30:
                    hallu_type = AbilityId.HALLUCINATION_IMMORTAL
            else:
                if sentry.health + sentry.shield < 30:
                    hallu_type = AbilityId.HALLUCINATION_IMMORTAL

            if hallu_type is not None:
                self.last_hallu_time = time
                return [CombatAction(sentry, None, False, ability=hallu_type)]

        result = self.use_guardian_shield(enemies, sentry, time)
        if len(result) > 0:
            return result

        return self.use_force_field(enemies, sentry, time)

    def use_force_field(self, enemies: EnemyData, sentry: Unit, time: float):
        force_field_is_good_idea = self.last_force_field_time + self.force_field_cooldown < time
        for key, value in self.tag_shield_used_dict.items():
            if value + 5 < time:
                # Some sentry has used its shield, it might be a good idea to use FF now
                force_field_is_good_idea = True

        if not force_field_is_good_idea:
             return [] # Hard priorizationg for guardian shield.

        relevant_enemies = enemies.close_enemies.not_structure.not_flying\
            .exclude_type(UnitValue.worker_types).exclude_type(UnitTypeId.SIEGETANKSIEGED)

        if sentry.energy < FORCE_FIELD_ENERGY_COST or relevant_enemies.amount < 5 or enemies.enemy_power.ground_presence < 15:
            return []

        center = relevant_enemies.center

        if self.last_force_field_time + 2 > time and len(self.last_force_field_positions) > self.last_force_fields_used:
            index = self.last_force_fields_used
            position = self.last_force_field_positions[index]
            if sentry.distance_to(position) < 9:
                self.last_force_fields_used += 1
                self.knowledge.print(f"JOINING FORCE FIELDS {position}!")
                return [CombatAction(sentry, position, False, ability= AbilityId.FORCEFIELD_FORCEFIELD)]
            else:
                self.knowledge.print(f"TOO FAR AWAY TO JOIN FORCE FIELDS {position}!")
                return[CombatAction(sentry, position, False)]

        if self.last_force_field_time + self.force_field_cooldown < time:
            point: Point2 = relevant_enemies.closest_to(sentry).position
            target_center = point.towards(center, 3)
            distance = sentry.distance_to(target_center)

            if distance < 9:
                # Activate force fields!
                self.last_force_field_time = time
                self.last_force_fields_used = 1
                point = sentry.position
                point = target_center.towards(point, 1)
                direction_v = target_center.offset( (-point.x, -point.y))
                perpenticular_v = Point2((direction_v.y, -direction_v.x))

                if enemies.powered_enemies(UnitTypeId.ZERGLING).amount - 10 > enemies.powered_enemies.amount:
                    if enemies.powered_enemies.amount > 10:
                        self.last_force_field_positions = self.ff_pos(target_center, direction_v, perpenticular_v, ff_centercube)
                    else:
                        self.last_force_field_positions = self.ff_pos(target_center, direction_v, perpenticular_v, ff_triangle)

                elif enemies.enemy_power.ground_presence > 25:
                    # Only use 5x FF against huge masses
                    self.last_force_field_positions = self.ff_pos(target_center, direction_v, perpenticular_v, ff_wall5)
                else:
                    self.last_force_field_positions = self.ff_pos(target_center, direction_v, perpenticular_v, ff_wall3)
                self.knowledge.print(f"Force fields ordered to: {self.last_force_field_positions}")

                return [CombatAction(sentry, self.last_force_field_positions[0], False,
                                     ability=AbilityId.FORCEFIELD_FORCEFIELD)]
        return []

    def ff_pos(self, center: Point2, direction: Point2, perpenticular: Point2, ff_type: List[Point2]) -> List[Point2]:
        list = []
        for adjust in ff_type:
            x = center.x + direction.x * adjust.y + perpenticular.x * adjust.x
            y = center.y + direction.y * adjust.y + perpenticular.y * adjust.x
            list.append(Point2((x, y)))
        return list

    def use_guardian_shield(self, enemies: EnemyData, sentry: Unit, time: float):
        if sentry.has_buff(BuffId.GUARDIANSHIELD):
            return []

        if self.tag_shield_used_dict.get(sentry.tag, 0) + self.shield_cooldown < time:
            for key, value in self.tag_shield_used_dict.items():
                if value + 3 < time:
                    # Another sentry just used it's shield, wait a while
                    return []

            enemies_at_close_range = enemies.close_enemies.closer_than(GUARDIAN_SHIELD_TRIGGER_RANGE,
                                                                       sentry.position)
            shooter_power = 0
            for enemy in enemies_at_close_range:  # type: Unit
                if self.unit_values.is_ranged_unit(enemy):
                    shooter_power += self.unit_values.power(enemy)

            if shooter_power > 3:
                self.tag_shield_used_dict[sentry.tag] = time
                return [CombatAction(sentry, None, False, ability=AbilityId.GUARDIANSHIELD_GUARDIANSHIELD)]
        return []

ff_wall3 = [
    Point2((0, 0)), Point2((3.25, -1)), Point2((-3.25, -1))
]

ff_wall5 = [
    Point2((0, 0)), Point2((3.25, -1)), Point2((-3.25, -1)), Point2((6.5, -2)), Point2((-6.5, -2))
]

ff_triangle = [
    Point2((-1.6, -1.4)), Point2((1.6, -1.4)), Point2((0, 1.4))
]

ff_centercube = [
    Point2((-1.6, -1.6)), Point2((1.6, -1.6)), Point2((-1.6, 1.6)) , Point2((1.6, 1.6))
]

ff_leftcube = [
    Point2((-1.6*2, -1.6)), Point2((0, -1.6)), Point2((-1.6 * 2, 1.6)) , Point2((0, 1.6))
]

ff_rightcube = [
    Point2((1.6*2, -1.6)), Point2((0, -1.6)), Point2((1.6 * 2, 1.6)) , Point2((0, 1.6))
]
