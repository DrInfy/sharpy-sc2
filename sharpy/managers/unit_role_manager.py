from typing import List, Union, Set, Iterable

from sharpy.managers.manager_base import ManagerBase
from sc2 import UnitTypeId, Race
from sc2.client import Client
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from sharpy.general.extended_power import ExtendedPower
from sharpy.managers.roles import UnitTask
from sharpy.managers.roles.units_in_role import UnitsInRole


class UnitRoleManager(ManagerBase):
    MAX_VALUE = 10

    def __init__(self):
        super().__init__()

        self.chat_count = 0
        self.had_task_set: Set[int] = set()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)

        # Peace units aren't drawn back to defend
        if knowledge.my_race == Race.Zerg:
            self.peace_unit_types = [UnitTypeId.OVERLORD, UnitTypeId.TRANSPORTOVERLORDCOCOON, UnitTypeId.OVERLORDTRANSPORT]
        else:
            self.peace_unit_types = []

        self.roles: List[UnitsInRole] = []
        self.roles.append(UnitsInRole(UnitTask.Idle, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Building, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Gathering, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Scouting, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Moving, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Fighting, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Defending, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Attacking, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Reserved, self.cache, self.ai))
        self.roles.append(UnitsInRole(UnitTask.Hallucination, self.cache, self.ai))

    def attack_ended(self):
        attackers = self.roles[UnitTask.Attacking.value].units
        self.roles[UnitTask.Idle.value].register_units(attackers)
        self.roles[UnitTask.Attacking.value].clear()

    def set_tasks(self, task: UnitTask, units: Units):
        for i in range(0, UnitRoleManager.MAX_VALUE):
            if i == task.value:
                self.roles[i].register_units(units)
            else:
                self.roles[i].remove_units(units)

        for unit in units:
            if unit.tag not in self.had_task_set:
                self.had_task_set.add(unit.tag)

    def is_in_role(self, task: UnitTask, unit: Unit) -> bool:
        return unit.tag in self.roles[task.value].tags

    def set_task(self, task: UnitTask, unit: Unit):
        if unit.tag not in self.had_task_set:
            self.had_task_set.add(unit.tag)
        for i in range(0, UnitRoleManager.MAX_VALUE):
            if i == task.value:
                self.roles[i].register_unit(unit)
            else:
                self.roles[i].remove_unit(unit)

    def clear_tasks(self, units: Union[Units, Iterable[int]]):
        for unit in units:
            self.clear_task(unit)

    def clear_task(self, unit: Union[Unit, int]):
        if type(unit) is int:
            # Use current iteration of the unit
            unit = self.cache.by_tag(unit)
            if unit is None:
                return  # Unit doesn't exist, do nothing

        for i in range(0, UnitRoleManager.MAX_VALUE):
            if i == UnitTask.Idle.value:
                self.roles[i].register_unit(unit)
            else:
                self.roles[i].remove_unit(unit)

    def units(self, task: UnitTask) -> Units:
        return self.roles[task.value].units

    @property
    def attacking_units(self) -> Units:
        """Returns all units that are currently attacking."""
        attacking_units = self.roles[UnitTask.Attacking.value].units.copy()
        moving_units = self.roles[UnitTask.Moving.value].units.copy()
        # Combine lists
        attacking_units.extend(moving_units)
        return attacking_units

    @property
    def hallucinated_units(self) -> Units:
        """Returns all units that are hallucinations."""
        return self.roles[UnitTask.Hallucination.value].units

    @property
    def idle(self) -> Units:
        """Short cut to roles[Idle].units"""
        return self.roles[UnitTask.Idle.value].units

    def get_defenders(self, power: ExtendedPower, position: Point2 ) -> Units:
        units = Units([], self.ai)
        current_power = ExtendedPower(self.unit_values)

        self._defenders_from(UnitTask.Idle, current_power, position, power, units)
        self._defenders_from(UnitTask.Moving, current_power, position, power, units)
        self._defenders_from(UnitTask.Fighting, current_power, position, power, units)
        self._defenders_from(UnitTask.Attacking, current_power, position, power, units)
        return units

    def _defenders_from(self, task: UnitTask, current_power: ExtendedPower, position: Point2, power: ExtendedPower, units: Units):
        """ Get defenders from a task. """
        if current_power.is_enough_for(power):
            return

        exclude_types = []
        exclude_types.append(UnitTypeId.OVERSEER)
        exclude_types.extend(self.knowledge.unit_values.worker_types)
        exclude_types.extend(self.peace_unit_types)

        role_units = self.roles[task.value].units\
            .exclude_type(exclude_types)

        unit: Unit
        for unit in role_units.sorted_by_distance_to(position):
            enough_air_power = current_power.air_power >= power.air_presence * 1.1
            enough_ground_power = current_power.ground_power >= power.ground_presence * 1.1

            if not self.unit_values.can_shoot_air(unit) and not enough_air_power and enough_ground_power:
                # Don't pull any more units that can't actually shoot the targets
                continue

            if not self.unit_values.can_shoot_ground(unit) and enough_air_power and not enough_ground_power:
                # Don't pull any more units that can't actually shoot the targets
                continue

            current_power.add_unit(unit)
            units.append(unit)
            if current_power.is_enough_for(power):
                return
        return

    def all_from_task(self, task: UnitTask) -> Units:
        return Units(self.roles[task.value].units, self.ai)

    @property
    def free_units(self) -> Units:
        units: Units = Units(self.roles[UnitTask.Idle.value].units, self.ai)
        units.extend(self.roles[UnitTask.Moving.value].units)
        return units

    @property
    def idle_workers(self) -> Units:
        """ Free workers, ie. gathering minerals or gas, or idling, and not dedicated to defending or scouting."""
        units: Units = self.roles[UnitTask.Idle.value].units
        # Mules should not count for workers
        return units.of_type([UnitTypeId.DRONE, UnitTypeId.PROBE, UnitTypeId.SCV])

    @property
    def free_workers(self) -> Units:
        """ Free workers, ie. gathering minerals or gas, or idling, and not dedicated to defending or scouting."""
        units: Units = Units(self.roles[UnitTask.Idle.value].units, self.ai)
        units.extend(self.roles[UnitTask.Gathering.value].units)
        # Mules should not count for workers
        return units.of_type([UnitTypeId.DRONE, UnitTypeId.PROBE, UnitTypeId.SCV])

    # Always update at the start of loop
    async def update(self):
        left_over = self.ai.units
        if self.knowledge.my_race == Race.Zerg:
            left_over = left_over.exclude_type(UnitTypeId.LARVA)
            self.clear_tasks(left_over.of_type(UnitTypeId.OVERLORDCOCOON))

        for i in range(1, UnitRoleManager.MAX_VALUE):
            self.roles[i].update()
            left_over = left_over.tags_not_in(self.roles[i].tags)

        left_over = left_over.tags_not_in(self.had_task_set).exclude_type(UnitTypeId.ADEPTPHASESHIFT)

        self.roles[UnitTask.Idle.value].clear()
        gatherers = left_over.collecting
        self.roles[UnitTask.Gathering.value].register_units(gatherers)

        # Everything else goes to idle
        self.roles[UnitTask.Idle.value].register_units(left_over.tags_not_in(gatherers.tags))

        # reassign overlords and other to reserved so that they're not used for defense
        peace_units = left_over.of_type(self.peace_unit_types)
        self.set_tasks(UnitTask.Reserved, peace_units)

        unit: Unit
        builders = left_over.filter(lambda unit: unit.is_constructing_scv)
        self.set_tasks(UnitTask.Building, builders)

        self.had_task_set.clear()

    async def post_update(self):
        if self.debug: # and self.chat_count < self.ai.time / 15:
            self.chat_count += 1
            idle = len(self.roles[UnitTask.Idle.value].tags)
            building = len(self.roles[UnitTask.Building.value].tags)
            gathering = len(self.roles[UnitTask.Gathering.value].tags)
            scouting = len(self.roles[UnitTask.Scouting.value].tags)
            moving = len(self.roles[UnitTask.Moving.value].tags)
            fighting = len(self.roles[UnitTask.Fighting.value].tags)
            defending = len(self.roles[UnitTask.Defending.value].tags)
            attacking = len(self.roles[UnitTask.Attacking.value].tags)
            reserved = len(self.roles[UnitTask.Reserved.value].tags)
            hallucination = len(self.roles[UnitTask.Hallucination.value].tags)

            enemy_total_power: ExtendedPower = self.knowledge.enemy_units_manager.enemy_total_power
            power_text = f'{enemy_total_power.power} ({enemy_total_power.ground_power}/{enemy_total_power.air_power})'

            # msg = f'{self.ai.time_formatted} I{idle} B{building} G{gathering} S{scouting} M{moving} ' \
            #     f'F{fighting} D{defending} A{attacking} R{reserved} H{hallucination} ETP{power_text}'
            msg = f'I{idle} B{building} G{gathering} S{scouting} M{moving} ' \
                f'F{fighting} D{defending} A{attacking} R{reserved} H{hallucination}'
            client: Client  = self.ai._client
            client.debug_text_2d(msg, Point2((0.4, 0.1)), None, 16)

            #self.knowledge.print(msg)

