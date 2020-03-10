from typing import List, Dict, Optional

from sharpy.knowledges import Knowledge
from sharpy.plans.acts import ActBase
from sharpy.managers import CooldownManager, GroupCombatManager
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.managers.roles import UnitTask


class DarkTemplarAttack(ActBase):

    def __init__(self):
        self.dt_push_started = False
        self.ninja_dt_tag: Optional[int] = None
        self.attack_dt_tag: Optional[int] = None
        self.combat: GroupCombatManager = None
        super().__init__()

    async def start(self, knowledge: Knowledge):
        self.combat = knowledge.combat_manager
        return await super().start(knowledge)

    async def execute(self) -> bool:
        # Start dark templar attack
        dts = self.cache.own(UnitTypeId.DARKTEMPLAR).ready
        if dts.amount >= 2 and not self.dt_push_started:
            self.dt_push_started = True
            dts = dts.random_group_of(2)
            zone = self.knowledge.enemy_main_zone
            harash_dt = dts[0]
            attack_dt = dts[1]
            self.do(harash_dt.move(zone.center_location))
            self.do(attack_dt.attack(zone.center_location))
            self.knowledge.roles.set_task(UnitTask.Reserved, harash_dt)
            self.knowledge.roles.set_task(UnitTask.Reserved, attack_dt)
            self.ninja_dt_tag = harash_dt.tag
            self.attack_dt_tag = attack_dt.tag

        elif self.dt_push_started:
            await self.harash_with_dt()
            await self.attack_with_dt()

        return True

    async def attack_with_dt(self):
        attack_dt: Unit = self.cache.by_tag(self.attack_dt_tag)
        if attack_dt is not None:
            self.knowledge.roles.set_task(UnitTask.Reserved, attack_dt)
            await self.attack_command(attack_dt)

    async def attack_command(self, unit: Unit):
        self.combat.add_unit(unit)
        target = self.knowledge.enemy_start_location

        units: Units = self.knowledge.known_enemy_units
        units = units.not_flying
        if units:
            target = units.closest_to(unit).position

        self.combat.execute(target)

    async def harash_with_dt(self):
        harash_dt: Unit = self.cache.by_tag(self.ninja_dt_tag)
        if harash_dt is not None:
            self.knowledge.roles.set_task(UnitTask.Reserved, harash_dt)
            enemy_workers = self.cache.enemy_in_range(harash_dt.position, 15).of_type(
                [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE])
            if enemy_workers.exists:
                target = enemy_workers.closest_to(harash_dt)
                self.do(harash_dt.attack(target))
            elif harash_dt.shield_health_percentage < 1:
                await self.attack_command(harash_dt)
            elif harash_dt.distance_to(self.knowledge.enemy_start_location) < 5:
                self.knowledge.roles.clear_task(harash_dt)
                self.ninja_dt_tag = 0
            else:
                self.do(harash_dt.move(self.knowledge.enemy_start_location))
