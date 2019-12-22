from typing import List, Dict

from sharpy.managers import UnitValue
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from .state_step import StateStep
from sharpy.combat import CombatGoal, CombatAction, EnemyData
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId, AbilityId


class StateWarpPrism(StateStep):
    def __init__(self, knowledge: Knowledge):
        self.grid_vectors = [
            Point2((1, 1)),
            Point2((1, 0)),
            Point2((1, -1)),
            Point2((0, 1)),
            #Point2((0, 0)),
            Point2((0, -1)),
            Point2((-1, 1)),
            Point2((-1, 0)),
            Point2((-1, -1)),
            ]

        self.release_tags: Dict[int,float] = dict()
        self.tag_unloading: Dict[int, float] = dict()
        super().__init__(knowledge)

    def FinalSolve(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> CombatAction:
        prism = goal.unit
        warpgates: Units = self.knowledge.unit_cache.own(UnitTypeId.WARPGATE)

        count = len(warpgates)
        ready = 0
        for gate in warpgates:  # type: Unit
            if gate.is_transforming or self.cd_manager.is_ready(gate.tag, AbilityId.WARPGATETRAIN_ZEALOT):
                ready += 1

        if (ready > 2 and ready >= count and goal.unit.type_id == UnitTypeId.WARPPRISM and self.ai.supply_left > 3
                and self.cd_manager.is_ready(prism.tag, AbilityId.MORPH_WARPPRISMTRANSPORTMODE, 6)):
            # TODO: Is it safe to warp in?
            self.cd_manager.used_ability(prism.tag, AbilityId.MORPH_WARPPRISMPHASINGMODE)
            return CombatAction(goal.unit, None, False, AbilityId.MORPH_WARPPRISMPHASINGMODE)
        elif goal.unit.type_id == UnitTypeId.WARPPRISMPHASING:
            not_ready = self.knowledge.unit_cache.own(self.unit_values.gate_types).not_ready
            if self.cd_manager.is_ready(prism.tag, AbilityId.MORPH_WARPPRISMPHASINGMODE, 2.5) \
                    and (len(not_ready) < 1 or not_ready.closest_distance_to(prism) > 4):
                self.cd_manager.used_ability(prism.tag, AbilityId.MORPH_WARPPRISMTRANSPORTMODE)
                return CombatAction(goal.unit, None, False, AbilityId.MORPH_WARPPRISMTRANSPORTMODE)

        if prism.cargo_used:
            for passenger in prism.passengers:  # type: Unit
                if self.release_tags.get(passenger.tag, 0) < self.ai.time:
                    if (not self.ai.in_pathing_grid(prism)):
                        break

                    stop_drop = False

                    for enemy in enemies.close_enemies:  # type: Unit
                        if enemy.radius + 1 > prism.distance_to(enemy):
                            stop_drop = True
                            break

                    if stop_drop:
                        break

                    #return CombatAction(prism, passenger, False, AbilityId.UNLOADALLAT_WARPPRISM)
                    return CombatAction(prism, prism, False, AbilityId.UNLOADALLAT_WARPPRISM)

        if not enemies.powered_enemies.exists:
            return command

        # Let's find the safest position that's closest to enemies

        best_danger = self.knowledge.enemy_units_manager.danger_value(goal.unit, enemies.our_median)
        best_position = enemies.our_median

        if prism.cargo_left and prism.shield > 0 and prism.shield + prism.health > 50:
            best_score = 0
            best_unit = None
            for own_unit in enemies.our_units:  # type: Unit
                if own_unit.cargo_size > prism.cargo_left:
                    continue
                if own_unit.shield:
                    continue
                if own_unit.weapon_cooldown < 2:
                    continue
                if own_unit.distance_to(prism) > 12:
                    continue

                score = self.unit_values.ground_range(own_unit) * (1.1 - own_unit.health_percentage) \
                        * self.unit_values.power(own_unit) - 1

                if score > best_score:
                    best_score = score
                    best_unit = own_unit

            if best_unit is not None:
                self.release_tags[best_unit.tag] = self.ai.time + best_unit.weapon_cooldown / 22.4
                return CombatAction(goal.unit, best_unit, False, AbilityId.SMART)

        priority_units = enemies.our_units.of_type([UnitTypeId.COLOSSUS, UnitTypeId.IMMORTAL, UnitTypeId.ARCHON, UnitTypeId.HIGHTEMPLAR])

        for vector in self.grid_vectors:
            position: Point2 = goal.unit.position + vector * 3
            if position.distance_to_point2(enemies.our_median) > 8:
                # Don't go too far away from our units
                continue

            danger = self.knowledge.enemy_units_manager.danger_value(goal.unit, position)
            coverage = 0
            for unit in priority_units:  # type: Unit
                if unit.distance_to(vector) < 6:
                    coverage += self.unit_values.power_by_type(unit.type_id) * 10

            if danger < best_danger - coverage:
                best_danger = danger
                best_position = position

        return CombatAction(goal.unit, best_position, False)

    def solve_combat(self, goal: CombatGoal, command: CombatAction, enemies: EnemyData) -> List[CombatAction]:
        return []
