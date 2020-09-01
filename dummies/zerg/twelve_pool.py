from sharpy.general.extended_power import ExtendedPower
from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sharpy.knowledges import KnowledgeBot
from sc2 import BotAI, UnitTypeId, AbilityId, Race
from sc2.units import Units


class PlanZoneAttack2(PlanZoneAttack):
    def _start_attack(self, power: ExtendedPower, attackers: Units):
        drones = self.cache.own(UnitTypeId.DRONE).closest_n_units(self.knowledge.enemy_start_location, 10)
        self.retreat_multiplier = 0  # never retreat, never surrender

        for unit in drones:
            self.knowledge.roles.set_task(UnitTask.Attacking, unit)

        return super()._start_attack(power, attackers)


class TwelvePool(KnowledgeBot):
    """Zerg 12 pool cheese tactic"""

    def __init__(self):
        super().__init__("12pool")

    async def create_plan(self) -> BuildOrder:
        build_step_buildings = [
            # 12 Pool
            Step(None, ActBuilding(UnitTypeId.SPAWNINGPOOL, 1), UnitExists(UnitTypeId.SPAWNINGPOOL, 1)),
        ]

        finish = [
            Step(RequireCustom(lambda k: self.enemy_structures.flying.exists and self.supply_used > 30), BuildGas(2)),
            Expand(2),
            UnitExists(UnitTypeId.DRONE, 20),
            MorphLair(),
            UnitExists(UnitTypeId.DRONE, 30),
            BuildGas(4),
            ActBuilding(UnitTypeId.SPIRE),
            ZergUnit(UnitTypeId.MUTALISK, 10, priority=True),
        ]

        build_step_units = [
            # 12 Pool followed by overlord
            Step(
                UnitExists(UnitTypeId.SPAWNINGPOOL, 1),
                ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2),
                UnitExists(UnitTypeId.OVERLORD, 2),
            ),
            # TheMusZero
            Step(
                UnitExists(UnitTypeId.SPAWNINGPOOL, 1),
                ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 14),
                UnitExists(UnitTypeId.DRONE, 14),
            ),
            # Queen for more larvae
            # BuildStep(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 1), UnitExists(UnitTypeId.QUEEN, 1)),
            # Endless zerglings
            Step(UnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA), None),
        ]

        return BuildOrder(
            build_step_buildings,
            finish,
            build_step_units,
            AutoOverLord(),
            DistributeWorkers(),
            InjectLarva(),
            PlanWorkerOnlyDefense(),
            PlanZoneDefense(),
            PlanZoneGather(),
            PlanZoneAttack2(2),
            PlanFinishEnemy(),
        )


class LadderBot(TwelvePool):
    @property
    def my_race(self):
        return Race.Zerg
