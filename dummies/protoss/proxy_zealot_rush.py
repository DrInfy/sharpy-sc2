from sharpy.managers.building_solver import WallType
from sharpy.managers.roles import UnitTask

from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, SequentialList, StepBuildGas
from sharpy.knowledges import KnowledgeBot, Knowledge


from sc2.ids.upgrade_id import UpgradeId

from sc2 import BotAI, run_game, maps, Race, Difficulty, UnitTypeId
from sc2.position import Point2


class ProxyZealots(ActBase):
    def __init__(self):
        super().__init__()
        self.started_worker_defense = False
        self.all_out_started = False
        self.proxy_worker_tag = None
        self.init_proxy = False
        self.completed = False
        self.gather_point: Point2
        self.proxy_location: Point2
        
    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.proxy_location = self.ai.game_info.map_center.towards(self.ai.enemy_start_locations[0], 25)
        self.gather_point = self.pather.find_path(self.proxy_location, self.knowledge.enemy_start_location, 8)

    async def build_order(self):
        if not self.ai.structures(UnitTypeId.NEXUS).ready.exists:
            # Nexus down, no build order to use.
            return

        nexus = self.ai.structures(UnitTypeId.NEXUS).ready.first

        if self.ai.structures(UnitTypeId.PYLON).ready.exists:
            proxy_pylon = self.ai.structures(UnitTypeId.PYLON).ready.random
        ramp = self.ai.main_base_ramp

        proxy_pylon = self.proxy_location
        gateways = self.ai.structures(UnitTypeId.GATEWAY)

        selected = False

        already_building_pylon = self.ai.already_pending(UnitTypeId.PYLON)
        worker = self.get_worker()
        if not worker:
            return

        self.knowledge.roles.set_task(UnitTask.Reserved, worker)

        if not self.has_build_order(worker):
            if self.ai.can_afford(UnitTypeId.PYLON) and self.ai.supply_used + 7 > self.ai.supply_cap and self.ai.supply_cap < 200:
                if self.ai.supply_used + 2 > self.ai.supply_cap:
                    already_building_pylon = False
                if self.ai.structures(UnitTypeId.PYLON).amount < 1:
                    await self.ai.build(UnitTypeId.PYLON, proxy_pylon,
                                     build_worker=worker)
                if gateways.ready.amount > 1 and not self.ai.already_pending(UnitTypeId.PYLON):
                    await self.ai.build(UnitTypeId.PYLON, gateways.ready.first,
                                     build_worker=worker)

            if self.ai.supply_cap > 20:
                if gateways.amount < 4 and self.ai.can_afford(UnitTypeId.GATEWAY) and proxy_pylon is not None:
                    await self.ai.build(UnitTypeId.GATEWAY, near=proxy_pylon,
                                     build_worker=worker)

            if worker.tag not in self.ai.unit_tags_received_action:
                target = self.pather.find_weak_influence_ground(self.proxy_location, 10)
                self.pather.find_influence_ground_path(worker.position, target)
                self.ai.do(worker.move(self.proxy_location))

        if not selected and self.ai.can_afford(UnitTypeId.PROBE) and self.ai.workers.amount < 17 and len(nexus.orders) == 0:
            self.do(nexus.train(UnitTypeId.PROBE))

        if gateways.ready.amount > 0 and self.ai.can_afford(UnitTypeId.ZEALOT):
            for gate in gateways.ready:
                if (len(gate.orders) == 0):
                    self.ai.do(gate.train(UnitTypeId.ZEALOT))
                    return

    async def execute(self) -> bool:
        self.knowledge.gather_point = self.gather_point

        if self.ai.supply_used > 50 or self.completed:
            self.completed = True
            return True

        await self.build_order()
        return False

    def get_worker(self):
        if not self.ai.workers:
            return None
        worker = self.cache.by_tag(self.proxy_worker_tag)
        if worker:
            return worker

        worker = self.ai.workers.closest_to(self.proxy_location)
        self.proxy_worker_tag = worker.tag
        return worker


# Original creation made by fazias
class ProxyZealotRushBot(KnowledgeBot):
    def __init__(self):
        super().__init__("Sharp Knives")


    async def create_plan(self) -> BuildOrder:
        self.knowledge.building_solver.wall_type = WallType.ProtossMainProtoss
        attack = PlanZoneAttack(7)
        attack.retreat_multiplier = 0.3
        # attack.attack_started = True
        backup = BuildOrder([
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 30, include_pending=True),
                 skip_until=RequiredUnitExists(UnitTypeId.ASSIMILATOR, 1)),
            ChronoUnitProduction(UnitTypeId.VOIDRAY, UnitTypeId.STARGATE),
                ActDefensiveCannons(0, 1),

            SequentialList([
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 14),
                GridBuilding(UnitTypeId.PYLON, 1),
                StepBuildGas(1),
                GridBuilding(UnitTypeId.GATEWAY, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 20),
                GridBuilding(UnitTypeId.CYBERNETICSCORE, 1),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 21),
                ActExpand(2),
                ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                StepBuildGas(2),
                GridBuilding(UnitTypeId.PYLON, 1),
                BuildOrder(
                    [
                        AutoPylon(),
                        GateUnit(UnitTypeId.STALKER, 2, priority=True),
                        ActTech(UpgradeId.WARPGATERESEARCH),
                        [
                            ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 22),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 2),
                                 ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 44)),
                            StepBuildGas(3, skip=RequiredGas(300)),
                            Step(RequiredUnitExists(UnitTypeId.NEXUS, 3),
                                 ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS, 56)),
                            StepBuildGas(5, skip=RequiredGas(200)),
                        ],
                        SequentialList(
                            [
                                Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1),
                                     GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)),
                                GridBuilding(UnitTypeId.STARGATE, 1),
                                Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                                     ActTech(UpgradeId.CHARGE)),
                                Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                                     ActTech(UpgradeId.ADEPTPIERCINGATTACK)),
                            ]),
                        [
                            ActUnit(UnitTypeId.VOIDRAY, UnitTypeId.STARGATE, 20, priority=True)
                        ],
                        Step(RequiredTime(60 * 5), ActExpand(3)),
                        [
                            GateUnit(UnitTypeId.STALKER, 30)
                        ],
                        [
                            GridBuilding(UnitTypeId.GATEWAY, 4),
                            StepBuildGas(4, skip=RequiredGas(200)),
                            GridBuilding(UnitTypeId.STARGATE, 2),
                        ]
                    ])
            ]),

        ])
        proxy_zealots = ProxyZealots()

        return BuildOrder([
            SequentialList([
                Step(None, proxy_zealots,
                     skip=RequireCustom(lambda k: self.knowledge.lost_units_manager.own_lost_type(UnitTypeId.GATEWAY))),
                backup
            ]),
            [
                PlanDistributeWorkers(),
                PlanZoneDefense(),
                PlanZoneGather(),
                attack,
                PlanFinishEnemy(),
            ],
            ChronoUnitProduction(UnitTypeId.ZEALOT, UnitTypeId.GATEWAY)
        ])


class LadderBot(ProxyZealotRushBot):
    @property
    def my_race(self):
        return Race.Protoss
