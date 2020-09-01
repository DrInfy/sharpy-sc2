from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.require.supply import SupplyType
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot


class RoachHydraBuild(BuildOrder):
    def __init__(self):

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
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 23)),
            # Early zerglings
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4), None),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 28)),
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 12), None),
            # Queen for more larvae
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 1)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 35), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ActUnitOnce(UnitTypeId.ROACH, UnitTypeId.LARVA, 4), skip_until=Gas(25)),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 100), skip_until=Minerals(750)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 45), None),
            Step(None, ActUnit(UnitTypeId.HYDRALISK, UnitTypeId.LARVA, 7), skip=UnitReady(UnitTypeId.HYDRALISKDEN, 1),),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 24), None),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 50), None),
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 10), skip_until=Gas(25)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 70), None),
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA), skip=UnitReady(UnitTypeId.HYDRALISKDEN, 1)),
            # Endless hydralisk
            Step(None, ActUnit(UnitTypeId.HYDRALISK, UnitTypeId.LARVA), None),
        ]
        super().__init__([self.overlords, buildings, gas_related, units])


class RoachHydra(KnowledgeBot):
    """Zerg macro opener into longer game roach hydra """

    def __init__(self):
        super().__init__("Roach hydra")

    async def pre_step_execute(self):
        if self.minerals < 600 and self.vespene > 200:
            self.distribute.max_gas = 7
        else:
            self.distribute.max_gas = None

    async def create_plan(self) -> BuildOrder:

        worker_scout = Step(
            None,
            WorkerScout(),
            skip=RequireCustom(lambda k: len(self.enemy_start_locations) == 1),
            skip_until=Supply(20),
        )
        self.distribute = DistributeWorkers()

        return BuildOrder(
            RoachHydraBuild(),
            SequentialList(
                PlanCancelBuilding(),
                PlanZoneGather(),
                PlanZoneDefense(),
                worker_scout,
                SpreadCreep(),
                InjectLarva(),
                self.distribute,
                PlanZoneAttack(),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(RoachHydra):
    @property
    def my_race(self):
        return Race.Zerg
