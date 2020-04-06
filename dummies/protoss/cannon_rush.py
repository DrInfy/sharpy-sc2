import random
from math import floor
from typing import List, Optional

from sc2.unit import Unit
from sharpy.managers.building_solver import WallType
from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot, Knowledge
from sharpy.utils import select_build_index

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class ProxyCannoneer(ActBase):
    pylons: List[Point2]

    def __init__(self):
        super().__init__()
        self.proxy_worker_tag: Optional[int] = None
        self.proxy_worker_tag2: Optional[int] = None

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.enemy_main: Point2 = self.knowledge.expansion_zones[-1].center_location
        self.natural: Point2 = self.knowledge.expansion_zones[-2].center_location

        self.enemy_ramp = self.knowledge.enemy_base_ramp
        d = self.enemy_main.distance_to(self.natural)
        height = self.ai.get_terrain_height(self.natural)
        self.between = self.natural.towards(self.enemy_main, 5)

        for i in range(4, floor(d)):
            pos = self.natural.towards(self.enemy_main, i + 2).rounded
            if height == self.ai.get_terrain_height(pos):
                self.between = pos

        self.pylons: List[Point2] = [
            self.natural,
            self.enemy_ramp.bottom_center.towards(self.between, 2).towards(self.natural, 1),
            self.enemy_ramp.top_center.towards(self.enemy_main, 4),
        ]

        if knowledge.enemy_race != Race.Zerg:
            self.pylons.append(self.between.towards(self.enemy_main, 6))
            self.pylons.append(self.enemy_ramp.top_center.towards(self.enemy_main, 8))
            self.pylons.append(self.enemy_main.towards(self.enemy_ramp.top_center, 4))
        else:
            self.pylons.append(self.enemy_main.towards(self.enemy_ramp.top_center, 10))

    async def execute(self) -> bool:
        worker = self.get_worker()
        cannon_worker = self.get_cannon_worker()
        if not worker and not cannon_worker:
            return True

        if cannon_worker:
            await self.micro_cannon_worker(cannon_worker)
        if worker:
            await self.micro_pylon_worker(worker)
        return False

    async def micro_cannon_worker(self, worker):
        self.knowledge.roles.set_task(UnitTask.Reserved, worker)

        if self.has_build_order(worker):
           return

        target_index = self.get_cannon_index()

        target = self.pylons[target_index]
        distance = worker.distance_to(target)
        if distance > 20:
            self.ai.do(worker.move(target))
        elif self.knowledge.can_afford(UnitTypeId.PHOTONCANNON):
            if distance < 5:
                if not self.has_build_order(worker):

                    await self.ai.build(UnitTypeId.PHOTONCANNON, target, max_distance=5, build_worker=worker)
            else:
                position = self.pather.find_weak_influence_ground(target, 4)
                target = self.pather.find_influence_ground_path(worker.position, position)
                self.ai.do(worker.move(target))
        else:
            position = self.pather.find_weak_influence_ground(target, 15)
            target = self.pather.find_influence_ground_path(worker.position, position)
            self.ai.do(worker.move(target))

    async def micro_pylon_worker(self, worker):
        self.knowledge.roles.set_task(UnitTask.Reserved, worker)
        if self.has_build_order(worker):
           return

        cannon_index = self.get_cannon_index()
        target_index = self.get_index()

        if target_index >= len(self.pylons):
            # Pylons are done
            position = self.pather.find_weak_influence_ground(worker.position, 15)
            target = self.pather.find_influence_ground_path(worker.position, position)
            self.ai.do(worker.move(target))
            return

        target = self.pylons[target_index]
        distance = worker.distance_to(target)

        mid_target = (worker.position + target) * 0.5
        if distance > 20:
            self.ai.do(worker.move(target))
        elif cannon_index + 1 < target_index:
            position = self.pather.find_weak_influence_ground(mid_target, 10)
            target = self.pather.find_influence_ground_path(worker.position, position)
            self.ai.do(worker.move(target))
        elif self.knowledge.can_afford(UnitTypeId.PYLON):
            if distance < 5:
                await self.ai.build(UnitTypeId.PYLON, target, max_distance=4, build_worker=worker, placement_step=1)
            else:
                position = self.pather.find_weak_influence_ground(target, 4)
                target = self.pather.find_influence_ground_path(worker.position, position)
                self.ai.do(worker.move(target))
        else:
            position = self.pather.find_weak_influence_ground(mid_target, 10)
            target = self.pather.find_influence_ground_path(worker.position, position)
            self.ai.do(worker.move(target))

    def get_index(self):
        pylons = self.cache.own(UnitTypeId.PYLON)
        index = 0
        if not pylons:
            return index

        i = 0
        for position in self.pylons:
            i += 1
            if pylons.closer_than(4, position).amount >= 1:
                index = i
        return index

    def get_cannon_index(self):
        cannons = self.cache.own(UnitTypeId.PHOTONCANNON)
        index = 0
        if not cannons:
            return index
        i = 0
        for position in self.pylons:
            i += 1
            count = 1
            if i > 2:
                count = 2
            if cannons.closer_than(5, position).amount >= count:
                index = i
        return min(index, len(self.pylons) - 1)

    def get_worker(self) -> Optional[Unit]:
        if self.ai.time < 0:
            return None  # wait a while
        worker = self.cache.by_tag(self.proxy_worker_tag)
        if worker:
            return worker

        available_workers = self.knowledge.roles.free_workers
        if not available_workers:
            return None

        worker = available_workers.closest_to(self.knowledge.enemy_start_location)
        self.proxy_worker_tag = worker.tag
        return worker

    def get_cannon_worker(self) -> Optional[Unit]:
        if self.ai.time < 25:
            return None  # wait a while
        worker = self.cache.by_tag(self.proxy_worker_tag2)
        if worker:
            return worker

        available_workers = self.knowledge.roles.free_workers
        if not available_workers:
            return None

        worker = available_workers.closest_to(self.knowledge.enemy_start_location)
        self.proxy_worker_tag2 = worker.tag
        return worker

class CannonRush(KnowledgeBot):

    def __init__(self):
        super().__init__("Sharp Cannon")

    async def create_plan(self) -> BuildOrder:
        rnd = select_build_index(self.knowledge, "build.cannon_rush", 0, 2)
        self.knowledge.building_solver.wall_type = WallType.NoWall
        rush_killed = RequireCustom(lambda k: self.knowledge.lost_units_manager.own_lost_type(UnitTypeId.PROBE) >= 3 or
                                    self.time > 4 * 60)

        if rnd == 2:
           cannon_rush = self.cannon_expand()
        elif rnd == 1:
           cannon_rush = self.cannon_contain()
        else:
           cannon_rush = self.cannon_rush()

        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 16), skip_until=RequiredUnitReady(UnitTypeId.PYLON, 1)),
            ChronoAnyTech(0),
            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 13),
                GridBuilding(UnitTypeId.PYLON, 1),
                Step(None, cannon_rush, skip=rush_killed),
                BuildOrder(
                    [
                        [
                            ActExpand(2),
                            ProtossUnit(UnitTypeId.PROBE, 30),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                        ],
                        GridBuilding(UnitTypeId.GATEWAY, 2),
                        GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                        StepBuildGas(2),
                        AutoPylon(),
                        ProtossUnit(UnitTypeId.STALKER, 4, priority=True),
                        StepBuildGas(3, skip=RequiredGas(300)),
                        ActTech(UpgradeId.WARPGATERESEARCH),
                        BuildOrder([]).forge_upgrades_all,
                        Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), ActTech(UpgradeId.BLINKTECH)),
                        [
                            ProtossUnit(UnitTypeId.PROBE, 22),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 2),
                                 ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                            StepBuildGas(3, skip=RequiredGas(300))
                        ],
                        [
                            ProtossUnit(UnitTypeId.STALKER, 100)
                        ],
                        [
                            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)),
                            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.GATEWAY, 7)),
                            StepBuildGas(4, skip=RequiredGas(200)),
                        ]
                    ])

            ]),
            SequentialList(
                [
                    PlanCancelBuilding(),
                    PlanZoneDefense(),
                    PlanDistributeWorkers(),
                    PlanZoneGather(),
                    PlanZoneAttack(6),
                    PlanFinishEnemy(),
                ])
        ])

    def cannon_contain(self) -> ActBase:
        self.knowledge.print(f"Cannon contain", "Build")
        enemy_main = self.knowledge.expansion_zones[-1]
        natural = self.knowledge.expansion_zones[-2]
        enemy_ramp = self.knowledge.enemy_base_ramp

        return Step(None, BuildOrder(
            [
                [
                    ActUnitOnce(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                    GridBuilding(UnitTypeId.FORGE, 1),
                    ActUnitOnce(UnitTypeId.PROBE, UnitTypeId.NEXUS, 18),
                ],
                [
                    BuildPosition(UnitTypeId.PYLON, natural.center_location),
                    BuildPosition(UnitTypeId.PHOTONCANNON, natural.center_location.towards(enemy_ramp.bottom_center, 5),
                                  exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PYLON, natural.center_location.towards(enemy_ramp.bottom_center, 8),
                                  exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, natural.center_location.towards(enemy_ramp.top_center, 13),
                                  exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PYLON,
                                  natural.center_location.towards(enemy_ramp.bottom_center, 16), exact=False,
                                  only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON,
                                  natural.center_location.towards(enemy_ramp.top_center, 20), exact=False,
                                  only_once=True),
                ],
                [
                    BuildPosition(UnitTypeId.PYLON, natural.behind_mineral_position_center, exact=False,
                                  only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON,
                                  natural.center_location.towards(enemy_main.behind_mineral_position_center, 5),
                                  exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PYLON,
                                  natural.center_location.towards(enemy_main.behind_mineral_position_center, 8),
                                  exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON,
                                  natural.center_location.towards(enemy_main.behind_mineral_position_center, 12),
                                  exact=False, only_once=True),

                    BuildPosition(UnitTypeId.PYLON,
                                  natural.center_location.towards(enemy_main.behind_mineral_position_center, 16),
                                  exact=False,
                                  only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON,
                                  natural.center_location.towards(enemy_main.behind_mineral_position_center, 20),
                                  exact=False,
                                  only_once=True),
                ],
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
            ]),
        # Skip cannon rushing if we started nexus, or have over 750 minerals, the build is probably stuck
        skip=RequiredAny([RequiredUnitExists(UnitTypeId.NEXUS, 2), RequiredMinerals(750)]))

    def cannon_rush(self) -> ActBase:
        self.knowledge.print(f"Cannon rush", "Build")
        return BuildOrder([
            [
                GridBuilding(UnitTypeId.PYLON, 1),
                GridBuilding(UnitTypeId.FORGE, 1, priority=True),
            ],

            ProxyCannoneer(),
            ProtossUnit(UnitTypeId.PROBE, 18),
            ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
            [
                Step(RequiredMinerals(400), GridBuilding(UnitTypeId.GATEWAY, 1)),
                Step(RequiredMinerals(700), ActExpand(2), skip=RequiredUnitExists(UnitTypeId.NEXUS, 2)),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
            ]
        ])

    def cannon_expand(self) -> ActBase:
        self.knowledge.print(f"Cannon expand", "Build")
        enemy_main = self.knowledge.expansion_zones[-1]
        natural = self.knowledge.expansion_zones[-2]
        enemy_ramp = self.knowledge.enemy_base_ramp
        pylon_pos: Point2 = natural.behind_mineral_position_center

        return BuildOrder(
            [
                [
                    ActUnitOnce(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                    GridBuilding(UnitTypeId.FORGE, 1),

                    ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 18),
                ],
                [
                    BuildPosition(UnitTypeId.PYLON, pylon_pos, exact=False,
                                  only_once=True),
                    Step(None,
                    BuildPosition(UnitTypeId.PHOTONCANNON,
                                  pylon_pos.towards(natural.center_location, 4),
                                  exact=False, only_once=True),
                         skip=RequireCustom(lambda k: k.lost_units_manager.own_lost_type(UnitTypeId.PYLON) > 0))
                    ,
                    ActExpand(2),
                    GridBuilding(UnitTypeId.GATEWAY, 1),
                    ActDefensiveCannons(2, 0, 1),
                ]
            ])

class LadderBot(CannonRush):
    @property
    def my_race(self):
        return Race.Protoss
