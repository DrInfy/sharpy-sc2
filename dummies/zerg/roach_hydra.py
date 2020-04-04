from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.require.required_supply import SupplyType
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot


class RoachHydraBuild(BuildOrder):
    def __init__(self):

        gas_related = [
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 2), ActTech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=RequiredGas(100)),
            Step(None, ActBuilding(UnitTypeId.ROACHWARREN, 1), skip_until=RequiredGas(100)),
            StepBuildGas(2, RequiredTime(4 * 60), RequiredGas(100)),
            StepBuildGas(3, RequiredUnitExists(UnitTypeId.HYDRALISKDEN, 1), RequiredGas(50)),
            StepBuildGas(4, RequiredSupply(60, SupplyType.Workers), RequiredGas(25)),
            StepBuildGas(6, RequiredMinerals(749), RequiredGas(25)),
            StepBuildGas(8, RequiredMinerals(1000), RequiredGas(25)),
        ]
        buildings = [
            Step(RequiredUnitExists(UnitTypeId.DRONE, 14), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(RequiredSupply(16), ActExpand(2)),
            Step(RequiredSupply(18), ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            StepBuildGas(1, RequiredSupply(20)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2), skip_until=RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1)),

            Step(RequiredUnitExists(UnitTypeId.DRONE, 24, include_killed=True, include_pending=True), ActExpand(3)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3)),
            Step(None, MorphLair(), skip=RequiredUnitExists(UnitTypeId.HIVE, 1)),
            Step(RequiredUnitExists(UnitTypeId.DRONE, 30, include_killed=True), ActExpand(4)),
            Step(RequiredUnitReady(UnitTypeId.LAIR, 1), ActBuilding(UnitTypeId.HYDRALISKDEN, 1)),
            MorphOverseer(1),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4)),
            Step(RequiredSupply(100), ActExpand(5)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 10), skip_until=RequiredMinerals(500)), # anti air defense!
        ]

        units = [
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 1), None),

            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 23)),

            # Early zerglings
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4),
                 None),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 28)),
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 12),
                 None),

            # Queen for more larvae
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 1)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 35), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ActUnitOnce(UnitTypeId.ROACH, UnitTypeId.LARVA, 4), skip_until=RequiredGas(25)),

            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 100), skip_until=RequiredMinerals(750)),

            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 45), None),
            Step(None, ActUnit(UnitTypeId.HYDRALISK, UnitTypeId.LARVA, 7), skip=RequiredUnitReady(UnitTypeId.HYDRALISKDEN, 1)),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 24), None),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 50), None),
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 10), skip_until=RequiredGas(25)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 70), None),

            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA), skip=RequiredUnitReady(UnitTypeId.HYDRALISKDEN, 1)),

            # Endless hydralisk
            Step(None, ActUnit(UnitTypeId.HYDRALISK, UnitTypeId.LARVA), None)
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

        worker_scout = Step(None, WorkerScout(), skip=RequireCustom(
            lambda k: len(self.enemy_start_locations) == 1), skip_until=RequiredSupply(20))
        self.distribute = PlanDistributeWorkers()

        return BuildOrder([
            RoachHydraBuild(),
            SequentialList([
                PlanCancelBuilding(),
                PlanZoneGather(),
                PlanZoneDefense(),
                worker_scout,
                SpreadCreep(),
                InjectLarva(),
                self.distribute,
                PlanZoneAttack(),
                PlanFinishEnemy()
            ]),
        ])


class LadderBot(RoachHydra):
    @property
    def my_race(self):
        return Race.Zerg
