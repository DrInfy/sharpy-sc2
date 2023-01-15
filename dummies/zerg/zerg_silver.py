from typing import Optional, List

from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sc2.position import Point2
from sharpy.interfaces import IZoneManager, IGameAnalyzer
from sharpy.knowledges import KnowledgeBot
from sharpy.managers.extensions import BuildDetector, ChatManager
from sharpy.managers.extensions.game_states import AirArmy
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.require.supply import SupplyType
from sharpy.plans.tactics import *
from sharpy.plans.tactics.weak import WeakAttack, WeakDefense
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas, IfElse
from sc2.ids.upgrade_id import UpgradeId


class RoachHydraBuild(BuildOrder):
    zone_manager: IZoneManager
    worker_rushed: bool

    def __init__(self):
        self.worker_rushed = False

        gas_related = [
            Step(UnitExists(UnitTypeId.HATCHERY, 2), Tech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=Gas(100),),
            Step(None, ActBuilding(UnitTypeId.ROACHWARREN, 1), skip_until=Gas(100)),
            StepBuildGas(2, Time(4 * 60), Gas(100)),
            StepBuildGas(3, UnitExists(UnitTypeId.HYDRALISKDEN, 1), Gas(50)),
            StepBuildGas(4, Supply(60, SupplyType.Workers), Gas(25)),
            StepBuildGas(6, Minerals(749), Gas(25)),
            StepBuildGas(8, Minerals(1000), Gas(25)),
        ]
        buildings = [
            Step(UnitExists(UnitTypeId.DRONE, 14), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(Supply(16), Expand(2)),
            Step(Supply(18), ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            StepBuildGas(1, Supply(20)),
            Step(
                None,
                ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2),
                skip_until=UnitExists(UnitTypeId.SPAWNINGPOOL, 1),
            ),
            # anti rush
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 4), skip_until=Gas(25)),
            Step(
                None,
                ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 10, priority=True),
                skip=lambda k: self.rush_detected,
                skip_until=Gas(25),
            ),
            Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 20), skip=lambda k: self.rush_detected),
            # end anti rush
            Step(UnitExists(UnitTypeId.DRONE, 24, include_killed=True, include_pending=True), Expand(3)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3)),
            Step(None, MorphLair(), skip=UnitExists(UnitTypeId.HIVE, 1)),
            Step(UnitExists(UnitTypeId.DRONE, 30, include_killed=True), Expand(4)),
            Step(UnitReady(UnitTypeId.LAIR, 1), ActBuilding(UnitTypeId.HYDRALISKDEN, 1)),
            MorphOverseer(1),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4)),
            Step(Supply(100), Expand(5)),
            Step(
                None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 10), skip_until=Minerals(500)
            ),  # anti air defense!
        ]

        units = [
            Step(UnitExists(UnitTypeId.HATCHERY, 1), None),
            Step(
                None,
                ZergUnit(UnitTypeId.ZERGLING, 6),
                skip=lambda k: not self.worker_rushed,
                skip_until=UnitReady(UnitTypeId.SPAWNINGPOOL, 1),
            ),
            Step(None, ZergUnit(UnitTypeId.DRONE, 23)),
            # Early zerglings
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ZergUnit(UnitTypeId.ZERGLING, 4), None),
            Step(None, ZergUnit(UnitTypeId.DRONE, 28)),
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ZergUnit(UnitTypeId.ZERGLING, 12), None),
            # Queen for more larvae
            Step(None, ZergUnit(UnitTypeId.QUEEN, 1)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 35), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 100), skip_until=Minerals(750)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 45), None),
            Step(None, ZergUnit(UnitTypeId.HYDRALISK, 7), skip=UnitReady(UnitTypeId.HYDRALISKDEN, 1),),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 24), None),
            Step(None, ZergUnit(UnitTypeId.DRONE, 50), None),
            Step(None, ZergUnit(UnitTypeId.ROACH, 10), skip_until=Gas(25)),
            Step(None, ZergUnit(UnitTypeId.DRONE, 70), None),
            Step(None, ZergUnit(UnitTypeId.ROACH), skip=UnitReady(UnitTypeId.HYDRALISKDEN, 1)),
            # Endless hydralisk
            Step(None, ZergUnit(UnitTypeId.HYDRALISK), None),
        ]

        zergling_response = IfElse(lambda k: self.worker_rushed, ZergUnit(UnitTypeId.ZERGLING, 6))
        queens_response = IfElse(lambda k: self.air_rush_detected, ZergUnit(UnitTypeId.QUEEN, 7, priority=True))

        super().__init__([self.overlords, zergling_response, queens_response, buildings, gas_related, units])

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.zone_manager = knowledge.get_required_manager(IZoneManager)
        self.build_detector = knowledge.get_required_manager(BuildDetector)
        self.game_analyzer = knowledge.get_required_manager(IGameAnalyzer)

    @property
    def rush_detected(self) -> bool:
        return self.build_detector.rush_detected

    @property
    def air_rush_detected(self) -> bool:
        return (
            len(self.ai.structures(UnitTypeId.HYDRALISKDEN).ready) > 0 and self.game_analyzer.enemy_power.air_power > 3
        )

    async def execute(self) -> bool:
        if not self.worker_rushed and self.ai.time < 120:
            self.worker_rushed = (
                len(
                    self.cache.enemy_workers.filter(
                        lambda u: u.distance_to(self.ai.start_location)
                        < u.distance_to(self.zone_manager.enemy_start_location)
                    )
                )
                > 0
            )

        return await super().execute()


class ZergSilver(KnowledgeBot):
    def __init__(self):
        super().__init__("Silver Zerg")
        self.attack = WeakAttack(30)

    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        self.client.game_step = 20
        return [BuildDetector(), ChatManager()]

    async def create_plan(self) -> BuildOrder:
        self.knowledge.data_manager.set_build("bio")

        worker_scouting = Step(
            None,
            WorkerScout(),
            skip=RequireCustom(lambda k: len(self.enemy_start_locations) == 1),
            skip_until=Supply(20),
        )

        tactics = [
            MineOpenBlockedBase(),
            WeakDefense(),
            worker_scouting,
            SpreadCreep(),
            InjectLarva(),
            DistributeWorkers(),
            PlanZoneGather(),
            self.attack,
            PlanFinishEnemy(),
        ]

        return CounterTerranTie([RoachHydraBuild(), tactics])


class LadderBot(ZergSilver):
    @property
    def my_race(self):
        return Race.Zerg
