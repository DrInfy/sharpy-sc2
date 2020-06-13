from sc2 import UnitTypeId, Race

from sharpy.knowledges import KnowledgeBot
from sharpy.plans import BuildOrder, Step, SequentialList
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *


class SpineDefender(KnowledgeBot):
    """Zerg dummy bot that creates a spine crawler and not much else."""

    def __init__(self):
        super().__init__("Spine defender")

    async def create_plan(self) -> BuildOrder:
        tactics = SequentialList(
            [
                # TauntEnemy(),
                # worker_scout,
                InjectLarva(),
                PlanHeatOverseer(),
                PlanWorkerOnlyDefense(),
                PlanZoneDefense(),
                PlanZoneGather(),
                PlanZoneAttack(),
                PlanFinishEnemy(),
            ]
        )

        return BuildOrder(
            [
                [
                    ZergUnit(UnitTypeId.DRONE, 14),
                    ZergUnit(UnitTypeId.OVERLORD, 2),
                    ActBuilding(UnitTypeId.SPAWNINGPOOL),
                    ZergUnit(UnitTypeId.DRONE, 20),
                    ZergUnit(UnitTypeId.ZERGLING, 20),
                ],
                [
                    Step(
                        UnitReady(UnitTypeId.SPAWNINGPOOL),
                        DefensiveBuilding(UnitTypeId.SPINECRAWLER, DefensePosition.Entrance, 0),
                    ),
                    ZergUnit(UnitTypeId.QUEEN, 2),
                ],
                [Step(UnitReady(UnitTypeId.SPAWNINGPOOL), AutoOverLord())],
                tactics,
            ]
        )


class LadderBot(SpineDefender):
    @property
    def my_race(self):
        return Race.Zerg
