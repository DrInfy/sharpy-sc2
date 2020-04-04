from typing import List

from sharpy.plans.acts import *
from sharpy.plans.acts.terran import *
from sharpy.plans.require import *
from sharpy.plans.require.required_supply import SupplyType
from sharpy.plans.tactics import *
from sharpy.plans.tactics.terran import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import BotAI, UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import Knowledge, KnowledgeBot
from sc2.position import Point2


class BuildBio(BuildOrder):
    def __init__(self):
        self.worker_rushed = False
        self.rush_bunker = BuildPosition(UnitTypeId.BUNKER, Point2((0,0)), exact=True)
        viking_counters = [UnitTypeId.COLOSSUS, UnitTypeId.MEDIVAC, UnitTypeId.RAVEN, UnitTypeId.VOIDRAY,
                           UnitTypeId.CARRIER, UnitTypeId.TEMPEST, UnitTypeId.BROODLORD]

        warn = WarnBuildMacro([
            (UnitTypeId.SUPPLYDEPOT, 1, 18),
            (UnitTypeId.BARRACKS, 1, 42),
            (UnitTypeId.REFINERY, 1, 44),
            (UnitTypeId.COMMANDCENTER, 2, 60 + 44),
            (UnitTypeId.BARRACKSREACTOR, 1, 120),
            (UnitTypeId.FACTORY, 1, 120 + 21),
        ], [])

        scv = [
            Step(None, TerranUnit(UnitTypeId.MARINE, 2, priority=True), skip_until=lambda k: self.worker_rushed),
            Step(None, MorphOrbitals(), skip_until=RequiredUnitReady(UnitTypeId.BARRACKS, 1)),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 16 + 6),
                 skip=RequiredUnitExists(UnitTypeId.COMMANDCENTER, 2)),
            Step(None, ActUnit(UnitTypeId.SCV, UnitTypeId.COMMANDCENTER, 32 + 12))
        ]

        dt_counter = [
            Step(RequiredAny([RequiredEnemyBuildingExists(UnitTypeId.DARKSHRINE),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.DARKTEMPLAR),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.BANSHEE)]), None),
            Step(None, GridBuilding(UnitTypeId.ENGINEERINGBAY, 1)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.Entrance, 2)),
            Step(None, DefensiveBuilding(UnitTypeId.MISSILETURRET, DefensePosition.CenterMineralLine, None))
        ]
        dt_counter2 = [
            Step(RequiredAny([RequiredEnemyBuildingExists(UnitTypeId.DARKSHRINE),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.DARKTEMPLAR),
                              RequiredEnemyUnitExistsAfter(UnitTypeId.BANSHEE)]), None),
            Step(None, GridBuilding(UnitTypeId.STARPORT, 2)),
            Step(None, ActBuildAddon(UnitTypeId.STARPORTTECHLAB, UnitTypeId.STARPORT, 1)),
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), ActUnit(UnitTypeId.RAVEN, UnitTypeId.STARPORT, 2)),
        ]

        opener = [
            Step(RequiredSupply(13), GridBuilding(UnitTypeId.SUPPLYDEPOT, 1, priority=True)),
            GridBuilding(UnitTypeId.BARRACKS, 1, priority=True),
            StepBuildGas(1, RequiredSupply(15)),
            TerranUnit(UnitTypeId.REAPER, 1, only_once=True, priority=True),
            Step(None, ActExpand(2), skip_until=RequiredAny([
                RequireCustom(lambda k: not k.possible_rush_detected),
                RequiredUnitExists(UnitTypeId.SIEGETANK, 2, include_killed=True)
            ])),
            Step(None, CancelBuilding(UnitTypeId.COMMANDCENTER, 1), skip=RequiredAny([
                RequireCustom(lambda k: not k.possible_rush_detected),
                RequiredUnitExists(UnitTypeId.SIEGETANK, 2, include_killed=True)
            ])),

            Step(None, self.rush_bunker, skip_until=lambda k: k.possible_rush_detected),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 2), skip_until=lambda k: k.possible_rush_detected),
            GridBuilding(UnitTypeId.SUPPLYDEPOT, 2, priority=True),
            ActBuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 1),
            GridBuilding(UnitTypeId.FACTORY, 1),
            ActBuildAddon(UnitTypeId.FACTORYTECHLAB, UnitTypeId.FACTORY, 1),

            AutoDepot()
        ]

        buildings = [
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 2)),
            Step(RequiredUnitReady(UnitTypeId.FACTORYTECHLAB), TerranUnit(UnitTypeId.SIEGETANK, 1)),
            StepBuildGas(2),
            # BuildStep(None, GridBuilding(UnitTypeId.ARMORY, 1)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 1)),
            Step(None, GridBuilding(UnitTypeId.STARPORT, 1)),
            Step(None, GridBuilding(UnitTypeId.BARRACKS, 3)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSTECHLAB, UnitTypeId.BARRACKS, 2)),

            Step(RequiredSupply(40, SupplyType.Workers), ActExpand(3)),

            Step(None, GridBuilding(UnitTypeId.BARRACKS, 5)),
            Step(None, ActBuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 3)),

            Step(None, ActBuildAddon(UnitTypeId.STARPORTREACTOR, UnitTypeId.STARPORT, 1)),
            StepBuildGas(4),
        ]

        tech = [
            Step(None, ActTech(UpgradeId.PUNISHERGRENADES)),
            Step(None, ActTech(UpgradeId.STIMPACK)),
            Step(None, ActTech(UpgradeId.SHIELDWALL)),
        ]

        mech = [
            TerranUnit(UnitTypeId.SIEGETANK, 2, priority=True)
        ]

        air = [
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 2, priority=True)),
            Step(None, TerranUnit(UnitTypeId.VIKINGFIGHTER, 1, priority=True)),
            Step(None, TerranUnit(UnitTypeId.VIKINGFIGHTER, 3, priority=True), skip_until=self.RequireAnyEnemyUnits(viking_counters, 1)),
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 4, priority=True)),
            Step(None, TerranUnit(UnitTypeId.VIKINGFIGHTER, 10, priority=True), skip_until=self.RequireAnyEnemyUnits(viking_counters, 4)),
            Step(RequiredUnitReady(UnitTypeId.STARPORT, 1), TerranUnit(UnitTypeId.MEDIVAC, 6, priority=True)),
        ]

        marines = [
            Step(RequiredUnitExists(UnitTypeId.REAPER, 1, include_killed=True), TerranUnit(UnitTypeId.MARINE, 2)),
            BuildOrder([
                TerranUnit(UnitTypeId.MARAUDER, 20, priority=True),
                TerranUnit(UnitTypeId.MARINE, 20),
                Step(RequiredMinerals(250), TerranUnit(UnitTypeId.MARINE, 100))
            ]),
        ]

        use_money = BuildOrder([
            Step(RequiredMinerals(400), GridBuilding(UnitTypeId.BARRACKS, 8)),
            Step(RequiredMinerals(500), ActBuildAddon(UnitTypeId.BARRACKSREACTOR, UnitTypeId.BARRACKS, 6)),
        ])

        super().__init__([warn, scv, opener, buildings,
                          dt_counter, dt_counter2,
                          tech,
                          mech, air, marines,
                          use_money])

    async def start(self, knowledge: 'Knowledge'):
        self.rush_bunker.position = knowledge.base_ramp.ramp.barracks_in_middle
        await super().start(knowledge)

    async def execute(self) -> bool:
        if not self.worker_rushed and self.ai.time < 120:
            self.worker_rushed = self.knowledge.known_enemy_workers.filter(
                lambda u: u.distance_to(self.ai.start_location) < u.distance_to(self.knowledge.likely_enemy_start_location))

        return await super().execute()




class BioBot(KnowledgeBot):
    def __init__(self):
        super().__init__("Rusty Infantry")
        self.attack = PlanZoneAttack(26)

    async def create_plan(self) -> BuildOrder:
        self.knowledge.data_manager.set_build("bio")
        worker_scout = Step(None, WorkerScout(), skip_until=RequiredUnitExists(UnitTypeId.SUPPLYDEPOT, 1))
        tactics = [
            PlanCancelBuilding(),
            LowerDepots(),
            PlanZoneDefense(),
            worker_scout,
            Step(None, CallMule(50), skip=RequiredTime(5 * 60)),
            Step(None, CallMule(100), skip_until=RequiredTime(5 * 60)),
            Step(None, ScanEnemy(), skip_until=RequiredTime(5 * 60)),
            PlanDistributeWorkers(),
            ManTheBunkers(),
            Repair(),
            ContinueBuilding(),
            PlanZoneGatherTerran(),
            self.attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([
            BuildBio(),
            tactics
        ])


class LadderBot(BioBot):
    @property
    def my_race(self):
        return Race.Terran
