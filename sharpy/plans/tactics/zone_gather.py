from typing import Optional

from sc2 import AbilityId, UnitTypeId

import sc2
from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import ActBase
from sc2.position import Point2
from sc2.unit import Unit

from sharpy.managers.roles import UnitTask
from sharpy.knowledges import Knowledge
from sharpy.managers import UnitValue


class PlanZoneGather(ActBase):
    def __init__(self):
        super().__init__()

        self.gather_set: sc2.List[int] = []
        self.blocker_tag: Optional[int] = None

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.my_race = self.ai.race
        self.defender_types: list
        self.knowledge = knowledge
        self.unit_values: UnitValue = knowledge.unit_values
        self.gather_point = self.knowledge.gather_point

    def should_hold_position(self, target_position: Point2) -> bool:
        close_enemies = self.knowledge.known_enemy_units.filter(lambda u: not u.is_flying and not u.is_structure)
        if close_enemies.exists:
            enemy_near = close_enemies.closest_distance_to(target_position) < 7
            if not enemy_near:
                return False

            attackers = self.knowledge.roles.attacking_units
            if attackers:
                attacker_near = attackers.closest_distance_to(target_position) < 5
                return not attacker_near

            return True

        # No non-flying enemies around
        return False

    async def execute(self) -> bool:
        unit: Unit
        if self.gather_point != self.knowledge.gather_point:
            self.gather_set.clear()
            self.gather_point = self.knowledge.gather_point

        unit: Unit
        for unit in self.cache.own([sc2.UnitTypeId.GATEWAY, sc2.UnitTypeId.ROBOTICSFACILITY]) \
                .tags_not_in(self.gather_set):
            # Rally point is set to prevent units from spawning on the wrong side of wall in
            pos: Point2 = unit.position
            pos = pos.towards(self.knowledge.gather_point, 3)
            self.do(unit(sc2.AbilityId.RALLY_BUILDING, pos))
            self.gather_set.append(unit.tag)

        await self.manage_blocker()

        units = []
        units.extend(self.knowledge.roles.idle)

        for unit in units:
            if self.knowledge.should_attack(unit):
                d2 = unit.position.distance_to(self.gather_point)
                if d2 > 6.5:
                    self.combat.add_unit(unit)

        self.combat.execute(self.gather_point, MoveType.Assault)
        return True # Always non blocking

    async def manage_blocker(self):
        target_position = self.knowledge.gate_keeper_position
        if target_position is not None:
            if self.blocker_tag is not None:
                unit = self.cache.by_tag(self.blocker_tag)
                if unit is not None and self.knowledge.close_gates:
                    if unit.type_id in {UnitTypeId.STALKER, UnitTypeId.IMMORTAL} and self.cache.own(UnitTypeId.ZEALOT):
                        # Swap expensive blocker to a zaalot
                        new_blocker = self.get_blocker(self.ai, target_position)
                        if new_blocker is not None:
                            self.knowledge.roles.clear_task(unit)
                            # Register tag
                            unit = new_blocker
                            self.blocker_tag = unit.tag
                            self.knowledge.roles.set_task(UnitTask.Reserved, unit)
                    if self.should_hold_position(target_position):
                        if unit.distance_to(target_position) < 0.2:
                            self.do(unit.hold_position())
                        elif (self.knowledge.known_enemy_units_mobile.exists and
                              self.knowledge.known_enemy_units_mobile.closest_distance_to(unit) < 2):
                            self.do(unit.attack(target_position))
                        else:
                            self.do(unit.move(target_position))
                    else:
                        if self.knowledge.natural_wall:
                            chill_position = target_position
                        else:
                            top_center = self.knowledge.base_ramp.top_center
                            chill_position = target_position.towards(top_center, -1)

                        if unit.distance_to(chill_position) > 4:
                            self.do(unit.move(chill_position))
                        elif unit.orders and unit.orders[0].ability.id == AbilityId.HOLDPOSITION:
                            self.do(unit.stop())
                else:
                    await self.remove_gate_keeper()

            elif self.knowledge.close_gates:
                # We need someone to block our wall.
                unit = self.get_blocker(self.ai, target_position)
                if unit is not None:
                    # Register tag
                    self.blocker_tag = unit.tag
                    self.knowledge.roles.set_task(UnitTask.Reserved, unit)
                    self.do(unit.attack(target_position))

    async def remove_gate_keeper(self):
        if self.blocker_tag is not None:
            unit = self.cache.by_tag(self.blocker_tag)
            if unit is not None:
                self.do(unit.attack(self.knowledge.gather_point))
            self.knowledge.roles.clear_task(self.blocker_tag)
            self.blocker_tag = None

        main_zone = self.knowledge.expansion_zones[0]

        for unit in main_zone.known_enemy_units : # type: Unit
            if unit.is_flying or self.unit_values.defense_value(unit.type_id) == 0 or self.unit_values.is_worker(unit):
                # Unit doesn't require removing gate keeper
                continue

            # Dangerous enemy near our base!
            if self.knowledge.ai.get_terrain_height(unit) < main_zone.height:
                # It hasn't gone up the ramp yet.
                continue

            if self.knowledge.base_ramp.top_center.distance_to(unit.position) < 3.16:
                # Enemy is probaly stuck in the ramp entrance
                continue
            # Enemy is inside our base, remove gate keeper!
            return False

        return True

    def get_blocker(self, ai, position: Point2) -> Optional[Unit]:
        unit = self.get_blocker_type(sc2.UnitTypeId.ZEALOT, ai, position)
        if unit is None:
            unit = self.get_blocker_type(sc2.UnitTypeId.ADEPT, ai, position)
        # if unit is None:
        #     unit = self.get_blocker_type(sc2.UnitTypeId.STALKER, ai, position)
        if unit is None:
            unit = self.get_blocker_type(sc2.UnitTypeId.DARKTEMPLAR, ai, position)
        # if unit is None:
        #     unit = self.get_blocker_type(sc2.UnitTypeId.IMMORTAL, ai, position)
        return unit

    def get_blocker_type(self, unit_type: sc2.UnitTypeId, ai: sc2.BotAI, position: Point2) -> Optional[Unit]:
        units = self.knowledge.roles.free_units(unit_type).closer_than(15, position)
        if units.exists:
            return units.closest_to(position)
        return None
