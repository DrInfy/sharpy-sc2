import random

from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas

from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId

from sharpy.knowledges import Knowledge, KnowledgeBot


class LingSpeedBuild(BuildOrder):
    def __init__(self):

        gas_related = [
            StepBuildGas(1, RequiredUnitExists(UnitTypeId.HATCHERY, 2)),
            Step(None, ActTech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=RequiredGas(100)),
            Step(None, ActBuilding(UnitTypeId.ROACHWARREN, 1), skip_until=RequiredGas(100)),

        ]
        buildings = [
            Step(RequiredUnitExists(UnitTypeId.DRONE, 14), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(None, ActExpand(2)),
            Step(RequiredUnitExists(UnitTypeId.EXTRACTOR, 1), ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2), skip_until=RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1)),

            Step(RequiredUnitExists(UnitTypeId.DRONE, 24, include_killed=True), ActExpand(3)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3)),
            Step(RequiredUnitExists(UnitTypeId.DRONE, 30, include_killed=True), ActExpand(4)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4)),
            Step(RequiredMinerals(500), ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 10)), # anti air defense!
        ]

        units = [
            Step(RequiredUnitExists(UnitTypeId.HATCHERY, 1), None),

            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 20)),

            # Early zerglings
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 12),
                 None),
            # Queen for more larvae
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 1)),
            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 30), None),
            Step(None, ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ActUnitOnce(UnitTypeId.ROACH, UnitTypeId.LARVA, 4), skip_until=RequiredGas(25)),

            Step(None, ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 40), None),
            Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 16), None),
            Step(None, ActUnit(UnitTypeId.ROACH, UnitTypeId.LARVA, 10), skip_until=RequiredGas(25)),

            # Endless zerglings
            Step(None, ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA), None)
        ]
        super().__init__([self.overlords, buildings, gas_related, units])

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.knowledge.print(f"LingSpeed", "Build")


class LingFloodBuild(BuildOrder):
    def __init__(self):

        gas_related = [
            StepBuildGas(1, RequiredUnitExists(UnitTypeId.HATCHERY, 2)),
            Step(None, ActTech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=RequiredGas(100)),
        ]
        buildings = [
            # 12 Pool
            Step(None, ActBuilding(UnitTypeId.SPAWNINGPOOL, 1)),
            Step(RequiredUnitExists(UnitTypeId.ZERGLING, 4, include_killed=True), ActExpand(2)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 2)),
            Step(RequiredUnitExists(UnitTypeId.DRONE, 24, include_killed=True), ActExpand(3)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 3)),
            Step(RequiredUnitExists(UnitTypeId.DRONE, 30, include_killed=True), ActExpand(4)),
            Step(None, ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 4)),

        ]

        spire_end_game = [
            Step(RequiredAny([RequiredSupply(90), RequiredUnitExists(UnitTypeId.LAIR, 1)]), None),
            ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 35),
            MorphLair(),
            ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 40),
            StepBuildGas(3, None),
            ActBuilding(UnitTypeId.SPIRE, 1),
            ActUnit(UnitTypeId.MUTALISK, UnitTypeId.LARVA, 10, priority=True)
        ]

        units = [
            Step(None, None, RequiredUnitExists(UnitTypeId.HATCHERY, 1)),

            # 12 Pool followed by overlord
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2),
                 RequiredUnitExists(UnitTypeId.OVERLORD, 2)),

            # TheMusZero
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 14),
                 RequiredUnitExists(UnitTypeId.DRONE, 14)),

            # Early zerglings
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 4),
                 None),
            # Queen for more larvae
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.QUEEN, UnitTypeId.HATCHERY, 1),
                 RequiredUnitExists(UnitTypeId.QUEEN, 1)),
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 20),
                 None),
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnitOnce(UnitTypeId.ZERGLING, UnitTypeId.LARVA, 12),
                 None),

            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, 30),
                 None),
            # Endless zerglings
            Step(RequiredUnitExists(UnitTypeId.SPAWNINGPOOL, 1), ActUnit(UnitTypeId.ZERGLING, UnitTypeId.LARVA),
                 None)
        ]

        super().__init__([self.overlords, buildings, spire_end_game, gas_related, units])

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.knowledge.print(f"LingFlood", "Build")


class DummyZergAttack(ActBase):
    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.all_out_started = False
        self.unit_values = knowledge.unit_values

    async def execute(self) -> bool:

        defend = False

        for zone in self.knowledge.expansion_zones:
            if zone.is_ours and zone.is_under_attack:
                ground_units = zone.known_enemy_units.not_flying
                target = zone.known_enemy_units.closest_to(zone.center_location).position

                if zone.known_enemy_power.ground_presence > 0 and ground_units:
                    defend = True
                    for zl in self.ai.units.of_type([UnitTypeId.ZERGLING, UnitTypeId.ROACH, UnitTypeId.QUEEN, UnitTypeId.MUTALISK]):
                        self.combat.add_unit(zl)
                elif zone.known_enemy_units:
                    for zl in self.cache.own(UnitTypeId.QUEEN):
                        self.combat.add_unit(zl)

                self.combat.execute(target, MoveType.SearchAndDestroy)
                break  # defend the most important zone first

        if not defend:
            target = await self.select_attack_target()

            if self.all_out_started and len(self.cache.own(UnitTypeId.ZERGLING)) == 0:
                await self.ai.chat_send("attack end!")
                self.all_out_started = False

            if self.ai.time < 4 * 60:
                limit = 6
            elif self.ai.time < 7 * 60:
                limit = 12
            elif self.ai.time < 10 * 60:
                limit = 20
            else:
                limit = 25

            if not self.all_out_started and len(self.cache.own(UnitTypeId.ZERGLING).idle) >= limit:
                await self.ai.chat_send("attack start!")
                self.all_out_started = True

            if self.all_out_started:
                for zl in self.ai.units.of_type([UnitTypeId.ZERGLING, UnitTypeId.ROACH, UnitTypeId.MUTALISK]):
                    self.combat.add_unit(zl)

            self.combat.execute(target, MoveType.Assault)
        return True

    async def select_attack_target(self):
        if self.knowledge.known_enemy_structures.exists:
            target = self.knowledge.known_enemy_structures.closest_to(self.ai.start_location).position
        else:
            target = self.ai.enemy_start_locations[0]
            last_scout = 0
            for zone in self.knowledge.enemy_expansion_zones:
                if zone.is_enemys:
                    target = zone.center_location
                    break
                if last_scout > zone.last_scouted_center:
                    target = zone.center_location
                    last_scout = zone.last_scouted_center
                    if last_scout + 2 * 60 < self.ai.time:
                        break
        return target


class LingFlood(KnowledgeBot):
    """Zerg 12 pool cheese opener into longer game ling flood"""

    def __init__(self, macro=None):
        if macro is None:
            self.macro_build = bool(random.getrandbits(1))
        else:
            self.macro_build = macro

        if self.macro_build:
            super().__init__("Ling Expand Speed")
        super().__init__("Ling Flood")

    async def create_plan(self) -> BuildOrder:
        if self.macro_build:
            return self.macro()
        return self.aggressive()

    def macro(self) -> BuildOrder:
        worker_scout = Step(None, WorkerScout(), skip_until=RequireCustom(
            lambda k: len(self.enemy_start_locations) > 1))
        distribute = PlanDistributeWorkers()

        return BuildOrder([
            LingSpeedBuild(),
            SequentialList([
                worker_scout,
                SpreadCreep(),
                InjectLarva(),
                distribute,
                DummyZergAttack()
            ]),
        ])

    def aggressive(self) -> BuildOrder:
        worker_scout = Step(None, WorkerScout(), skip_until=RequireCustom(
            lambda k: len(self.enemy_start_locations) > 1))
        stop_gas = RequiredAny([RequiredGas(100), RequiredTechReady(UpgradeId.ZERGLINGMOVEMENTSPEED, 0.001)])
        end_game = RequiredAny([RequiredSupply(90), RequiredUnitExists(UnitTypeId.LAIR, 1)])

        return BuildOrder([
            LingFloodBuild(),
            SequentialList([
                worker_scout,
                SpreadCreep(),
                InjectLarva(),
                Step(None, PlanDistributeWorkers(3, 3), skip=RequiredAny([stop_gas, end_game])),
                Step(None, PlanDistributeWorkers(0, 0), skip_until=stop_gas, skip=end_game),
                Step(None, PlanDistributeWorkers(None, None), skip_until=end_game),
                DummyZergAttack()
            ]),
        ])


class LadderBot(LingFlood):
    @property
    def my_race(self):
        return Race.Zerg
