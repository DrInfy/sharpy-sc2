from typing import Optional

from sharpy.interfaces import ICombatManager, IZoneManager
from sharpy.knowledges import Knowledge
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit import Unit
from sc2.units import Units

from sharpy.managers.core.roles import UnitTask


class DarkTemplarAttack(ActBase):
    """
    Very old code, you probably don't want to use this for anything
    """

    combat: ICombatManager
    zone_manager: IZoneManager

    def __init__(self):
        self.dt_push_started = False
        self.ninja_dt_tag: Optional[int] = None
        self.attack_dt_tag: Optional[int] = None
        super().__init__()

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.combat = knowledge.get_required_manager(ICombatManager)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)

    async def execute(self) -> bool:
        # Start dark templar attack
        dts = self.cache.own(UnitTypeId.DARKTEMPLAR).ready
        if dts.amount >= 2 and not self.dt_push_started:
            self.dt_push_started = True
            dts = dts.random_group_of(2)
            zone = self.zone_manager.enemy_main_zone
            harash_dt = dts[0]
            attack_dt = dts[1]
            harash_dt.move(zone.center_location)
            attack_dt.attack(zone.center_location)
            self.roles.set_task(UnitTask.Reserved, harash_dt)
            self.roles.set_task(UnitTask.Reserved, attack_dt)
            self.ninja_dt_tag = harash_dt.tag
            self.attack_dt_tag = attack_dt.tag

        elif self.dt_push_started:
            await self.harash_with_dt()
            await self.attack_with_dt()

        return True

    async def attack_with_dt(self):
        attack_dt: Unit = self.cache.by_tag(self.attack_dt_tag)
        if attack_dt is not None:
            self.roles.set_task(UnitTask.Reserved, attack_dt)
            await self.attack_command(attack_dt)

    async def attack_command(self, unit: Unit):
        self.combat.add_unit(unit)
        target = self.zone_manager.enemy_start_location

        units: Units = self.ai.all_enemy_units
        units = units.not_flying
        if units:
            target = units.closest_to(unit).position

        self.combat.execute(target)

    async def harash_with_dt(self):
        harash_dt: Unit = self.cache.by_tag(self.ninja_dt_tag)
        if harash_dt is not None:
            self.roles.set_task(UnitTask.Reserved, harash_dt)
            enemy_workers = self.cache.enemy_in_range(harash_dt.position, 15).of_type(
                [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE]
            )
            if enemy_workers.exists:
                target = enemy_workers.closest_to(harash_dt)
                harash_dt.attack(target)
            elif harash_dt.shield_health_percentage < 1:
                await self.attack_command(harash_dt)
            elif harash_dt.distance_to(self.zone_manager.enemy_start_location) < 5:
                self.roles.clear_task(harash_dt)
                self.ninja_dt_tag = 0
            else:
                harash_dt.move(self.zone_manager.enemy_start_location)
