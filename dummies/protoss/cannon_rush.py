import random
from typing import List

from frozen.plans.acts import *
from frozen.plans.acts.protoss import *
from frozen.plans.require import *
from frozen.plans.tactics import *
from frozen.plans import BuildOrder, Step, SequentialList, StepBuildGas
from frozen.knowledges import KnowledgeBot

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2


class CannonRush(KnowledgeBot):

    def __init__(self):
        super().__init__("Sharp Cannon")

    async def create_plan(self) -> BuildOrder:
        rnd = random.randint(0, 2)
        if rnd == 2:
           cannon_rush = self.cannon_expand()
        elif rnd == 1:
           cannon_rush = self.cannon_rush()
        else:
           cannon_rush = self.cannon_contain()
        
        return BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 16), skip_until=RequiredUnitReady(UnitTypeId.PYLON, 1)),
            ChronoAnyTech(0),
            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 13),
                GridBuilding(UnitTypeId.PYLON, 1),
                cannon_rush,
                BuildOrder(
                    [
                        [
                            ActExpand(2),
                            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 30),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 2), ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                        ],
                        GridBuilding(UnitTypeId.GATEWAY, 2),
                        GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                        StepBuildGas(2),
                        AutoPylon(),
                        StepBuildGas(3, skip=RequiredGas(300)),
                        ActTech(UpgradeId.WARPGATERESEARCH, UnitTypeId.CYBERNETICSCORE),
                        BuildOrder([]).forge_upgrades_all,
                        Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), ActTech(UpgradeId.BLINKTECH, UnitTypeId.TWILIGHTCOUNCIL)),
                        [
                            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 2),
                                 ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                            StepBuildGas(3, skip=RequiredGas(300))
                        ],
                        [
                            GateUnit(UnitTypeId.STALKER, 100)
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
        enemy_main = self.knowledge.expansion_zones[-1]
        natural = self.knowledge.expansion_zones[-2]
        enemy_ramp = self.knowledge.enemy_base_ramp
        pylons: List[Point2] = [
            enemy_ramp.bottom_center.towards(natural.center_location, 3),
            enemy_ramp.top_center.towards(enemy_main.center_location, 3),
            enemy_ramp.top_center.towards(enemy_main.center_location, 6),
            enemy_ramp.top_center.towards(natural.center_location, -3),
            enemy_ramp.top_center.towards(enemy_main.center_location, 8),
            enemy_ramp.top_center.towards(natural.center_location, -6),
        ]

        return Step(None, BuildOrder(
            [
                [
                    ActUnitOnce(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                    GridBuilding(UnitTypeId.FORGE, 1),
                    ActUnitOnce(UnitTypeId.PROBE, UnitTypeId.NEXUS, 18),
                ],
                [
                    BuildPosition(UnitTypeId.PYLON, pylons[0], exact=False),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[1], exact=False, only_once=True),

                    BuildPosition(UnitTypeId.PYLON, pylons[2], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[3], exact=False, only_once=True),

                    BuildPosition(UnitTypeId.PYLON, pylons[4], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[5], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[4], exact=False, only_once=True),
                ],
                [
                    BuildPosition(UnitTypeId.PYLON, pylons[1], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[0], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PYLON, pylons[3], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[2], exact=False, only_once=True),

                    BuildPosition(UnitTypeId.PYLON, pylons[5], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[4], exact=False, only_once=True),
                    BuildPosition(UnitTypeId.PHOTONCANNON, pylons[5], exact=False, only_once=True),
                ],
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 16),
            ]),
        # Skip cannon rushing if we started nexus, or have over 750 minerals, the build is probably stuck
        skip = RequiredAny([RequiredUnitExists(UnitTypeId.NEXUS, 2), RequiredMinerals(750)]))

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