from typing import List

from sharpy.managers import GroupCombatManager
from sharpy.managers.combat2 import MoveType
from sharpy.plans.acts import *
from sharpy.plans.acts.zerg import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans.tactics.zerg import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sc2 import UnitTypeId, Race
from sc2.ids.upgrade_id import UpgradeId
from sc2.unit import Unit

from sharpy.knowledges import Knowledge, KnowledgeBot


class DummyZergAttack(ActBase):
    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.all_out_started = False
        self.unit_values = knowledge.unit_values
        self.combat_manager: GroupCombatManager = self.knowledge.combat_manager

    async def execute(self) -> bool:
        target = self.knowledge.enemy_start_location
        defend = False
        for zone in self.knowledge.expansion_zones:
            if zone.is_ours and zone.is_under_attack:
                ground_units = zone.known_enemy_units.not_flying
                if zone.known_enemy_power.ground_presence > 0 and ground_units:
                    defend = True
                    for zl in self.ai.units.of_type([UnitTypeId.ZERGLING, UnitTypeId.ROACH, UnitTypeId.QUEEN, UnitTypeId.MUTALISK]):
                        target = ground_units.closest_to(zone.center_location).position
                        self.combat_manager.add_unit(zl)
                elif zone.known_enemy_units:
                    for zl in self.cache.own(UnitTypeId.QUEEN):
                        target = zone.known_enemy_units.closest_to(zone.center_location).position
                        self.combat_manager.add_unit(zl)
                break  # defend the most important zone first

        if not defend:
            target = await self.select_attack_target()

            if self.all_out_started and len(self.cache.own(UnitTypeId.ZERGLING)) == 0:
                await self.ai.chat_send("attack end!")
                self.all_out_started = False

            if self.ai.time < 9 * 60:
                limit = 6
            elif self.ai.time < 13 * 60:
                limit = 12
            elif self.ai.time < 17 * 60:
                limit = 20
            else:
                limit = 25

            if not self.all_out_started and len(self.cache.own(UnitTypeId.ZERGLING).idle) >= limit:
                await self.ai.chat_send("attack start!")
                self.all_out_started = True

            if self.all_out_started:
                for zl in self.ai.units.of_type([UnitTypeId.ZERGLING, UnitTypeId.ROACH, UnitTypeId.MUTALISK]):
                    self.combat_manager.add_unit(zl)

        self.combat_manager.execute(target, MoveType.Assault)
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
            Step(RequiredAny([RequiredSupply(70), RequiredUnitExists(UnitTypeId.LAIR, 1)]), None),
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


class WorkerAttack(ActBase):
    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.all_out_started = False
        self.unit_values = knowledge.unit_values
        self.combat_manager: GroupCombatManager = self.knowledge.combat_manager
        self.combat_manager.prioritise_workers = True
        self.tags: List[int] = []

    async def execute(self) -> bool:
        if self.knowledge.iteration == 0:
            for worker in self.ai.workers:
                self.tags.append(worker.tag)

        if len(self.tags) == 0:
            return True

        attack_zone = self.knowledge.enemy_main_zone
        enemy_natural = self.knowledge.expansion_zones[-2]

        target = self.knowledge.enemy_start_location
        fighters = self.ai.workers.tags_in(self.tags)
        self.tags.clear()
        move_type = MoveType.Assault
        if self.knowledge.lost_units_manager.calculate_enemy_lost_resources()[0] < 50:
            target = attack_zone.behind_mineral_position_center
            move_type = MoveType.PanicRetreat
        else:
            target = self.ai.structures.closest_to(attack_zone.behind_mineral_position_center)
            move_type = MoveType.Assault

        for fighter in fighters: # type: Unit
            self.tags.append(fighter.tag)
            if fighter.health > 5 and fighter.distance_to(attack_zone.center_location) > 20:
                self.do(fighter.move(attack_zone.center_location))
            elif fighter.health < 6 and enemy_natural.mineral_fields.exists:
                mf = enemy_natural.mineral_fields.closest_to(fighter)
                self.do(fighter.gather(mf))
            else:
                if attack_zone.known_enemy_units.not_structure.closer_than(4, fighter).exists:
                    target = attack_zone.known_enemy_units.not_structure.closest_to(fighter).position
                    move_type = MoveType.Assault
                self.combat_manager.add_unit(fighter)

        self.combat_manager.execute(target, move_type)
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


class WorkerRush(KnowledgeBot):
    """Zerg super worker rush"""

    def __init__(self):
        super().__init__("Worker Rush Dummy")

    async def create_plan(self) -> BuildOrder:
        stop_gas = RequiredAny([RequiredGas(100), RequiredTechReady(UpgradeId.ZERGLINGMOVEMENTSPEED, 0.001)])
        end_game = RequiredAny([RequiredSupply(70), RequiredUnitExists(UnitTypeId.LAIR, 1)])

        return BuildOrder([
            ActUnitOnce(UnitTypeId.DRONE, UnitTypeId.LARVA, 24),
            LingFloodBuild(),
            SequentialList([
                InjectLarva(),
                Step(None, PlanDistributeWorkers(3, 3), skip=RequiredAny([stop_gas, end_game])),
                Step(None, PlanDistributeWorkers(0, 0), skip_until=stop_gas, skip=end_game),
                Step(None, PlanDistributeWorkers(None, None), skip_until=end_game),
                WorkerAttack(),
                DummyZergAttack()
            ]),
        ])


class LadderBot(WorkerRush):
    @property
    def my_race(self):
        return Race.Zerg
