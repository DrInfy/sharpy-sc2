from math import floor

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sharpy.interfaces import IBuildingSolver, ILostUnitsManager, IGatherPointSolver
from sharpy.managers.core.building_solver import WallType
from sharpy.managers.core.roles import UnitTask

from sharpy.managers.core import BuildingSolver
from sharpy.managers.core.building_solver import is_empty, is_free, fill_padding
from sharpy.managers.core.grids import BuildGrid, GridArea, Rectangle, BlockerType, BuildArea

from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot, Knowledge


from sc2.ids.upgrade_id import UpgradeId

from sc2.position import Point2


class ProxySolver(BuildingSolver):
    def massive_grid(self, pos):
        rect = Rectangle(pos.x, pos.y, 6, 9)
        unit_exit_rect = Rectangle(pos.x - 2, pos.y + 4, 2, 2)
        unit_exit_rect2 = Rectangle(pos.x + 6, pos.y + 4, 2, 2)
        padding = Rectangle(pos.x - 2, pos.y - 2, 10, 12)

        if (
            self.grid.query_rect(rect, is_empty)
            and self.grid.query_rect(unit_exit_rect, is_free)
            and self.grid.query_rect(unit_exit_rect2, is_free)
        ):
            pylons = [
                pos + Point2((1 + 2, 1)),
            ]
            gates = [
                pos + Point2((1.5, 3.5)),
                pos + Point2((4.5, 3.5)),
                pos + Point2((1.5, 6.5)),
                pos + Point2((4.5, 6.5)),
            ]
            for pylon_pos in pylons:
                self.fill_and_save(pylon_pos, BlockerType.Building2x2, BuildArea.Pylon)

            for gate_pos in gates:
                self.fill_and_save(gate_pos, BlockerType.Building3x3, BuildArea.Building)

            self.grid.fill_rect(padding, fill_padding)


class ProxyZealots(ActBase):
    gather_point_solver: IGatherPointSolver

    def __init__(self):
        super().__init__()
        self.started_worker_defense = False
        self.all_out_started = False
        self.proxy_worker_tag = None
        self.init_proxy = False
        self.completed = False
        self.gather_point: Point2
        self.proxy_location: Point2
        self.solver = ProxySolver()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.gather_point_solver = knowledge.get_required_manager(IGatherPointSolver)
        self.proxy_location = self.ai.game_info.map_center.towards(self.ai.enemy_start_locations[0], 25)
        self.solver.grid = BuildGrid(self.knowledge)

        center = Point2((floor(self.proxy_location.x), floor(self.proxy_location.y)))
        x_range = range(-18, 18)
        y_range = range(-18, 18)

        for x in x_range:
            for y in y_range:
                pos = Point2((x + center.x, y + center.y))
                area: GridArea = self.solver.grid[pos]

                if area is None:
                    continue

                self.solver.massive_grid(pos)
        if self.knowledge.debug:
            self.solver.grid.save("proxy.bmp")
        self.gather_point = self.pather.find_path(self.proxy_location, self.zone_manager.enemy_start_location, 8)
        self.solver.buildings2x2.sort(key=lambda x: self.proxy_location.distance_to(x))
        self.solver.buildings3x3.sort(key=lambda x: self.proxy_location.distance_to(x))

    async def build_order(self):
        count = self.cache.own(UnitTypeId.GATEWAY).amount
        if count == 4:
            if self.proxy_worker_tag:
                worker = self.get_worker()
                self.roles.clear_task(worker)
                self.proxy_worker_tag = None
            return

        if not self.ai.structures(UnitTypeId.NEXUS).ready.exists:
            # Nexus down, no build order to use.
            return

        if count < 4:
            await self.worker_micro()

    async def worker_micro(self):
        worker = self.get_worker()
        if not worker:
            return
        self.roles.set_task(UnitTask.Reserved, worker)
        if not self.has_build_order(worker):
            if self.ai.can_afford(UnitTypeId.PYLON):
                count = self.get_count(UnitTypeId.PYLON, include_pending=True)
                if count < 2:
                    for point in self.solver.buildings2x2:
                        if not self.ai.structures.closer_than(1, point):
                            if worker.build(UnitTypeId.PYLON, point):
                                break  # success

            if self.cache.own(UnitTypeId.PYLON).ready:
                count = self.get_count(UnitTypeId.GATEWAY, include_pending=True)
                if count < 4 and self.ai.can_afford(UnitTypeId.GATEWAY):
                    matrix = self.ai.state.psionic_matrix
                    for point in self.solver.buildings3x3:
                        if not self.ai.structures.closer_than(1, point) and matrix.covers(point):
                            if worker.build(UnitTypeId.GATEWAY, point):
                                break  # success

            if worker.tag not in self.ai.unit_tags_received_action and not self.has_build_order(worker):
                target = self.pather.find_weak_influence_ground(self.proxy_location, 10)
                self.pather.find_influence_ground_path(worker.position, target)
                worker.move(self.proxy_location)

    async def execute(self) -> bool:
        self.gather_point_solver.set_gather_point(self.gather_point)
        await self.build_order()
        return False

    def get_worker(self):
        if not self.ai.workers:
            return None
        worker = self.cache.by_tag(self.proxy_worker_tag)
        if worker:
            return worker

        worker = self.ai.workers.closest_to(self.proxy_location)
        self.proxy_worker_tag = worker.tag
        return worker


# Original creation made by fazias
class ProxyZealotRushBot(KnowledgeBot):
    def __init__(self):
        super().__init__("Sharp Knives")

    async def create_plan(self) -> BuildOrder:
        self.building_solver.wall_type = WallType.ProtossMainProtoss
        attack = PlanZoneAttack(7)
        attack.retreat_multiplier = 0.3
        # attack.attack_started = True
        backup = BuildOrder(
            Step(
                None,
                ChronoUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                skip=UnitExists(UnitTypeId.PROBE, 30, include_pending=True),
                skip_until=UnitExists(UnitTypeId.ASSIMILATOR, 1),
            ),
            ChronoUnit(UnitTypeId.VOIDRAY, UnitTypeId.STARGATE),
            DefensiveCannons(0, 1),
            SequentialList(
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                BuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 21),
                Expand(2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                BuildGas(2),
                GridBuilding(UnitTypeId.PYLON, 1),
                BuildOrder(
                    AutoPylon(),
                    ProtossUnit(UnitTypeId.STALKER, 2, priority=True),
                    Tech(UpgradeId.WARPGATERESEARCH),
                    [
                        ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                        Step(UnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                        StepBuildGas(3, skip=Gas(300)),
                        Step(UnitExists(UnitTypeId.NEXUS, 3), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 56)),
                        StepBuildGas(5, skip=Gas(200)),
                    ],
                    SequentialList(
                        Step(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1),),
                        GridBuilding(UnitTypeId.STARGATE, 1),
                        Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.CHARGE)),
                        Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.ADEPTPIERCINGATTACK)),
                    ),
                    [ActUnit(UnitTypeId.VOIDRAY, UnitTypeId.STARGATE, 20, priority=True)],
                    Step(Time(60 * 5), Expand(3)),
                    [ProtossUnit(UnitTypeId.STALKER, 30)],
                    [
                        GridBuilding(UnitTypeId.GATEWAY, 4),
                        StepBuildGas(4, skip=Gas(200)),
                        GridBuilding(UnitTypeId.STARGATE, 2),
                    ],
                ),
            ),
        )
        proxy = BuildOrder(
            [
                ProtossUnit(UnitTypeId.PROBE, 17),
                ProtossUnit(UnitTypeId.ZEALOT),
                GridBuilding(UnitTypeId.PYLON, 1, priority=True),
                Step(UnitReady(UnitTypeId.PYLON, 1), AutoPylon()),
                ProxyZealots(),
                ChronoUnit(UnitTypeId.ZEALOT, UnitTypeId.GATEWAY),
                [
                    DistributeWorkers(),
                    Step(None, SpeedMining(), lambda ai: ai.client.game_step > 5),
                    PlanZoneDefense(),
                    PlanZoneGather(),
                    attack,
                    PlanFinishEnemy(),
                ],
            ]
        )
        return BuildOrder(SequentialList(Step(None, proxy, skip=Once(Supply(50))), backup))


class LadderBot(ProxyZealotRushBot):
    @property
    def my_race(self):
        return Race.Protoss
