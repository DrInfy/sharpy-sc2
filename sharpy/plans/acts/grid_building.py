from typing import Optional

from sharpy.sc2math import to_new_ticks
from sc2.ids.buff_id import BuffId
from sc2.units import Units

import sc2
from sharpy.managers import BuildingSolver
from sharpy.managers.roles import UnitTask
from sharpy.utils import map_to_point2s_center
from sc2 import UnitTypeId, AbilityId, Race
from sc2.position import Point2
from sc2.unit import Unit, UnitOrder

from .act_building import ActBuilding


worker_trainers = {AbilityId.NEXUSTRAIN_PROBE, AbilityId.COMMANDCENTERTRAIN_SCV}


class GridBuilding(ActBuilding):

    def __init__(self, unit_type: UnitTypeId, to_count: int, iterator: Optional[int] = None, priority: bool = False,
                 allow_wall: bool = True):
        super().__init__(unit_type, to_count)
        self.allow_wall = allow_wall
        assert isinstance(priority, bool)
        self.priority = priority
        self.builder_tag: Optional[int] = None
        self.iterator: Optional[int] = iterator
        self.consider_worker_production = True
        self.building_solver: BuildingSolver = None
        self.make_pylon = None

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.building_solver = self.knowledge.building_solver

        if self.unit_type != UnitTypeId.PYLON:
            self.make_pylon: Optional[GridBuilding] = GridBuilding(UnitTypeId.PYLON, 0, 2)
            await self.make_pylon.start(knowledge)

    async def execute(self) -> bool:
        count = self.get_count(self.unit_type, include_pending=False, include_not_ready=True)

        if count >= self.to_count:
            if self.builder_tag is not None:
                self.knowledge.roles.clear_task(self.builder_tag)
                self.builder_tag = None

            return True  # Step is done

        if count + (self.pending_build(self.unit_type)
                    - self.cache.own(self.unit_type).not_ready.amount) >= self.to_count:
            if self.builder_tag is not None:
                worker = self.cache.by_tag(self.builder_tag)
                if worker is not None:
                    self.set_worker(worker)
                    await self.debug_draw()
            return True  # Building is ordered

        if self.knowledge.my_race == Race.Protoss:
            position = self.position_protoss(count)
        elif self.knowledge.my_race == Race.Terran:
            position = self.position_terran(count)
        else:
            raise ValueError(f'Position lookup for race {self.knowledge.my_race} not supported.')

        if position is None:
            if self.make_pylon is not None:
                self.make_pylon.to_count = len(self.cache.own(UnitTypeId.PYLON).ready) + 1
                await self.make_pylon.execute()
            return False  # Stuck and cannot proceed

        worker = self.get_worker(position)  # type: Unit

        if worker is None:
            return False  # Cannot proceed

        d = worker.distance_to(position)
        time = d / to_new_ticks(worker.movement_speed)
        unit = self.ai._game_data.units[self.unit_type.value]
        cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)

        wait_time = self.prequisite_progress()

        if self.knowledge.can_afford(self.unit_type):
            if wait_time <= 0:
                self.set_worker(worker)
                if worker.tag not in self.ai.unit_tags_received_action and not self.has_build_order(worker):
                    # No duplicate builds
                    if self.knowledge.my_race == Race.Protoss:
                        await self.build_protoss(worker, count, position)
                    elif self.knowledge.my_race == Race.Terran:
                        await self.build_terran(worker, count, position)
                return False

            if self.priority and wait_time < time:
                # Go wait
                self.set_worker(worker)
                self.knowledge.reserve(cost.minerals, cost.vespene)
                if not self.has_build_order(worker):
                    self.do(worker.move(self.adjust_build_to_move(position)))

        elif self.priority and wait_time < time:
            available_minerals = self.ai.minerals - self.knowledge.reserved_minerals
            available_gas = self.ai.vespene - self.knowledge.reserved_gas

            if self.consider_worker_production and self.knowledge.income_calculator.mineral_income > 0:
                for town_hall in self.ai.townhalls:  # type: Unit
                    # TODO: Zerg(?)
                    if town_hall.orders:
                        starting_next_probe_in = -50 / self.knowledge.income_calculator.mineral_income
                        order = town_hall.orders[0]  # Only consider first order
                        if order.ability.id in worker_trainers:
                            starting_next_probe_in += 12 * (1 - order.progress)

                        if starting_next_probe_in < time:
                            available_minerals -= 50  # should start producing workers soon now
                    else:
                        available_minerals -= 50  # should start producing workers soon now

            if available_minerals + time * self.knowledge.income_calculator.mineral_income >= cost.minerals \
                    and available_gas + time * self.knowledge.income_calculator.gas_income >= cost.vespene:
                # Go wait
                self.set_worker(worker)
                self.knowledge.reserve(cost.minerals, cost.vespene)

                if not self.has_build_order(worker):
                    self.do(worker.move(self.adjust_build_to_move(position)))

        return False

    def adjust_build_to_move(self, position: Point2) -> Point2:
        closest_zone = position.closest(map_to_point2s_center(self.knowledge.expansion_zones))
        return position.towards(closest_zone, 1)

    async def debug_actions(self):
        if self.builder_tag is not None:
            worker: Unit = self.cache.by_tag(self.builder_tag)

            if worker and worker.orders:
                moving_status = ""
                for order in worker.orders:
                    if moving_status != "":
                        moving_status += ", "
                    moving_status += order.ability.id.name
                self._client.debug_text_world(moving_status, worker.position3d)

    def get_worker(self, position: Point2):
        worker: Unit = None
        if self.builder_tag is None:
            if self.knowledge.my_race == Race.Protoss:
                builders: Units = self.knowledge.roles.all_from_task(UnitTask.Building)\
                    .filter(lambda w: not w.has_buff(BuffId.ORACLESTASISTRAPTARGET))

                if builders:
                    closest = None
                    best_distance = 0
                    for builder in builders:  # type: Unit
                        if len(builder.orders) == 1:
                            order: UnitOrder = builder.orders[0]
                            if order.target is Point2:
                                distance = position.distance_to_point2(order.target)
                            else:
                                distance = position.distance_to_point2(builder.position)
                            if distance < 10 and (closest is None or distance < best_distance):
                                best_distance = distance
                                closest = builder
                    worker = closest

            if worker is None:
                free_workers = self.knowledge.roles.free_workers\
                    .filter(lambda w: not w.has_buff(BuffId.ORACLESTASISTRAPTARGET))
                if self.knowledge.my_race == Race.Terran:
                    free_workers = free_workers.filter(lambda u: not self.has_build_order(u))
                if free_workers.exists:
                    worker = free_workers.closest_to(position)
        else:
            worker: Unit = self.cache.by_tag(self.builder_tag)
            if worker is None or worker.is_constructing_scv:
                # Worker is probably dead or it is already building something else.
                self.builder_tag = None
        return worker

    def set_worker(self, worker: Unit):
        self.knowledge.roles.set_task(UnitTask.Building, worker)
        self.builder_tag = worker.tag

    def clear_worker(self):
        if self.builder_tag is not None:
            self.knowledge.roles.clear_task(self.builder_tag)
            self.builder_tag = None

    def position_protoss(self, count) -> Optional[Point2]:
        is_pylon = self.unit_type == UnitTypeId.PYLON
        buildings = self.ai.structures
        matrix = self.ai.state.psionic_matrix
        future_position = None

        iterator = self.get_iterator(is_pylon, count)

        if is_pylon:
            for point in self.building_solver.pylon_position[::iterator]:
                if not buildings.closer_than(1, point):
                    return point
        else:
            pylons = self.cache.own(UnitTypeId.PYLON).not_ready
            for point in self.building_solver.building_position[::iterator]:
                if not self.allow_wall:
                    if point in self.building_solver.wall_buildings:
                        continue
                if not buildings.closer_than(1, point) and matrix.covers(point):
                    return point

                if future_position is None and pylons and point.distance_to_closest(pylons) <= 7:
                    future_position = point

        return future_position

    def position_terran(self, count) -> Optional[Point2]:
        is_depot = self.unit_type == UnitTypeId.SUPPLYDEPOT
        buildings = self.ai.structures
        future_position = None

        if is_depot:
            for point in self.building_solver.pylon_position:
                if not buildings.closer_than(1, point):
                    return point
        else:
            pylons = self.cache.own(UnitTypeId.PYLON).not_ready
            for point in self.building_solver.building_position:
                if not self.allow_wall:
                    if point in self.building_solver.wall_buildings:
                        continue
                if not buildings.closer_than(1, point):
                    return point

                if future_position is None and pylons and point.distance_to_closest(pylons) <= 7:
                    future_position = point

        return future_position

    def get_iterator(self, is_pylon, count):
        if self.iterator is None:
            if is_pylon and count < 14:
                return 2
            return 1

        return self.iterator

    async def build_protoss(self, worker: Unit, count, position: Point2):
        if self.has_build_order(worker):
            action = worker.build(self.unit_type, position, queue=True)

            for order in worker.orders:
                if order.ability.id == action.ability:
                    # Don't add the same order twice
                    return

            self.do(action)

        # try the selected position first
        err: sc2.ActionResult = await self.ai.synchronous_do(worker.build(self.unit_type, position))
        if not err:
            self.print(f"Building {self.unit_type.name} to {position}")
            return  # success

        is_pylon = self.unit_type == UnitTypeId.PYLON
        buildings = self.ai.structures
        matrix = self.ai.state.psionic_matrix
        iterator = self.get_iterator(is_pylon, count)

        if is_pylon:
            for point in self.building_solver.pylon_position[::iterator]:

                if not buildings.closer_than(1, point):
                    err: sc2.ActionResult = await self.ai.synchronous_do(worker.build(self.unit_type, point))
                    if not err:
                        return  # success
                    else:
                        pass
                        # self.knowledge.print("err !!!!" + str(err.value) + " " + str(err))
        else:
            for point in self.building_solver.building_position[::iterator]:
                if not buildings.closer_than(1, point) and matrix.covers(point):
                    err: sc2.ActionResult = await self.ai.synchronous_do(worker.build(self.unit_type, point))
                    if not err:
                        return  # success
                    else:
                        pass
                        # self.knowledge.print("err !!!!" + str(err.value) + " " + str(err))
        self.print("GRID POSITION NOT FOUND !!!!")

    async def build_terran(self, worker: Unit, count, position: Point2):
        if self.has_build_order(worker):
            action = worker.build(self.unit_type, position, queue=True)

            for order in worker.orders:
                if order.ability.id == action.ability:
                    # Don't add the same order twice
                    return

            self.do(action)

        # try the selected position first
        err: sc2.ActionResult = await self.ai.synchronous_do(worker.build(self.unit_type, position))
        if not err:
            self.print(f"Building {self.unit_type.name} to {position}")
            return  # success

        is_depot = self.unit_type == UnitTypeId.SUPPLYDEPOT
        buildings = self.ai.structures
        iterator = self.get_iterator(is_depot, count)

        if is_depot:
            for point in self.building_solver.pylon_position[::1]:

                if not buildings.closer_than(1, point):
                    err: sc2.ActionResult = await self.ai.synchronous_do(worker.build(self.unit_type, point))
                    if not err:
                        return  # success
                    else:
                        pass
                        # self.knowledge.print("err !!!!" + str(err.value) + " " + str(err))
        else:
            for point in self.building_solver.building_position[::1]:
                if not buildings.closer_than(1, point):
                    err: sc2.ActionResult = await self.ai.synchronous_do(worker.build(self.unit_type, point))
                    if not err:
                        return  # success
                    else:
                        pass
                        # self.knowledge.print("err !!!!" + str(err.value) + " " + str(err))
        self.print("GRID POSITION NOT FOUND !!!!")

    def prequisite_progress(self) -> float:
        """ Return progress in realtime seconds """
        # Protoss:
        if self.unit_type == UnitTypeId.GATEWAY or self.unit_type == UnitTypeId.FORGE:
            return self.building_progress(UnitTypeId.PYLON)

        if self.unit_type == UnitTypeId.CYBERNETICSCORE:
            return min(self.building_progress(UnitTypeId.GATEWAY), self.building_progress(UnitTypeId.WARPGATE))

        if self.unit_type == UnitTypeId.TWILIGHTCOUNCIL:
            return self.building_progress(UnitTypeId.CYBERNETICSCORE)

        if self.unit_type == UnitTypeId.TEMPLARARCHIVE:
            return self.building_progress(UnitTypeId.TWILIGHTCOUNCIL)

        if self.unit_type == UnitTypeId.TEMPLARARCHIVE:
            return self.building_progress(UnitTypeId.TWILIGHTCOUNCIL)

        if self.unit_type == UnitTypeId.STARGATE:
            return self.building_progress(UnitTypeId.CYBERNETICSCORE)

        if self.unit_type == UnitTypeId.FLEETBEACON:
            return self.building_progress(UnitTypeId.STARGATE)

        if self.unit_type == UnitTypeId.ROBOTICSFACILITY:
            return self.building_progress(UnitTypeId.CYBERNETICSCORE)

        if self.unit_type == UnitTypeId.ROBOTICSBAY:
            return self.building_progress(UnitTypeId.ROBOTICSFACILITY)

        if self.unit_type == UnitTypeId.PHOTONCANNON:
            return self.building_progress(UnitTypeId.FORGE)

        if self.unit_type == UnitTypeId.SHIELDBATTERY:
            return self.building_progress(UnitTypeId.CYBERNETICSCORE)

        # Terran:
        if self.unit_type == UnitTypeId.BARRACKS:
            return self.building_progress(UnitTypeId.SUPPLYDEPOT)
        if self.unit_type == UnitTypeId.FACTORY:
            return self.building_progress(UnitTypeId.BARRACKS)
        if self.unit_type == UnitTypeId.ARMORY:
            return self.building_progress(UnitTypeId.FACTORY)
        if self.unit_type == UnitTypeId.STARPORT:
            return self.building_progress(UnitTypeId.FACTORY)
        if self.unit_type == UnitTypeId.FUSIONCORE:
            return self.building_progress(UnitTypeId.STARPORT)

        return 0
