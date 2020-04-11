from sc2 import Race, UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import KnowledgeBot, Knowledge
from sharpy.plans import BuildOrder
from sharpy.plans.zerg import (
    CounterTerranTie,
    ZergUnit,
    Step,
    RequiredUnitExists,
    SequentialList,
    ActBuilding,
    ActExpand,
    AutoOverLord,
    StepBuildGas,
    ActUnit,
    RequiredSupply,
    RequiredGas,
    ActTech,
    PlanDistributeWorkers,
    OverlordScout,
    PlanFinishEnemy,
    PlanZoneAttack,
    InjectLarva,
    PlanZoneDefense,
    RequiredEnemyUnitExists,
    MorphRavager,
    PlanZoneGather,
)


class RoachBurrowBuild(BuildOrder):
    def __init__(self):
        super().__init__(
            SequentialList(
                # Opener
                Step(RequiredUnitExists(UnitTypeId.DRONE, 13), ZergUnit(UnitTypeId.OVERLORD, 2, priority=True)),
                Step(RequiredUnitExists(UnitTypeId.DRONE, 16), ActExpand(2, priority=True)),
                StepBuildGas(1),
                Step(RequiredSupply(17), ActBuilding(UnitTypeId.SPAWNINGPOOL)),
                Step(RequiredSupply(20), ZergUnit(UnitTypeId.QUEEN, 1, priority=True)),
                Step(RequiredSupply(20), ZergUnit(UnitTypeId.ZERGLING, 6)),
                Step(RequiredGas(100), ActTech(UpgradeId.BURROW)),
                Step(RequiredSupply(24), ActBuilding(UnitTypeId.ROACHWARREN)),
                Step(RequiredSupply(24), ZergUnit(UnitTypeId.QUEEN, 2, priority=True)),
                Step(RequiredSupply(27), ZergUnit(UnitTypeId.ROACH, 5)),
                StepBuildGas(2),
                Step(None, ZergUnit(UnitTypeId.ROACH, 999)),
            ),
            SequentialList(
                # Workers
                ZergUnit(UnitTypeId.DRONE, 25),
                # Step(self.zones_are_safe, ZergUnit(UnitTypeId.DRONE, 80), skip=self.ideal_workers_reached),
            ),
            SequentialList(
                # Overlords
                AutoOverLord(),
            ),
            # todo: make ravagers acording to the number of siege tanks
            # todo: how to make ravager morph priority?
            SequentialList(Step(RequiredEnemyUnitExists(UnitTypeId.SIEGETANK, 1), MorphRavager(2))),
        )

    # todo: turn into a require class?
    # def zones_are_safe(self, knowledge: Knowledge) -> bool:
    #     for zone in knowledge.zone_manager.expansion_zones:
    #         if zone.is_ours and zone.is_under_attack:
    #             return False
    #
    #     return knowledge.game_analyzer.army_can_survive

    # todo: turn into a require class?
    # def ideal_workers_reached(self, knowledge: Knowledge) -> bool:
    #     ideal_workers = 0
    #
    #     for townhall in self.ai.townhalls:
    #         ideal_workers += townhall.ideal_harvesters
    #     for gas in self.ai.gas_buildings:
    #         ideal_workers += gas.ideal_harvesters
    #
    #     current_workers = len(knowledge.unit_cache.own(UnitTypeId.DRONE))
    #
    #     return current_workers >= ideal_workers


class RoachBurrowBot(KnowledgeBot):
    """
    Dummy bot that rushes to roaches and burrow for an early timing attack.
    """

    def __init__(self):
        super().__init__("Blunt Burrow")

    async def create_plan(self) -> BuildOrder:
        return BuildOrder(
            CounterTerranTie([RoachBurrowBuild()]),
            SequentialList(
                OverlordScout(),
                PlanDistributeWorkers(),
                InjectLarva(),
                PlanZoneDefense(),
                PlanZoneGather(),
                PlanZoneAttack(8),
                PlanFinishEnemy(),
            ),
        )


class LadderBot(RoachBurrowBot):
    @property
    def my_race(self):
        return Race.Zerg
