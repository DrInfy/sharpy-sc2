from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import *
from sharpy.plans.acts.protoss import *
from sharpy.plans.require import *
from sharpy.plans.tactics import *
from sharpy.plans import BuildOrder, Step, StepBuildGas
from sharpy.knowledges import KnowledgeBot
from sc2 import BotAI, UnitTypeId, AbilityId, Race
from sc2.ids.upgrade_id import UpgradeId


class DtPush(ActBase):

    def __init__(self):
        super().__init__()
        self.dt_push_started = False
        self.ninja_dt_tag = None

    async def execute(self) -> bool:
        # Start dark templar attack
        dts = self.cache.own(UnitTypeId.DARKTEMPLAR).ready
        if dts.amount >= 2 and not self.dt_push_started:
            self.dt_push_started = True
            dts = dts.random_group_of(2)
            zone = self.knowledge.enemy_main_zone
            harash_dt = dts[0]
            attack_dt = dts[1]
            self.do(harash_dt.move(zone.center_location))
            self.do(attack_dt.attack(zone.center_location))
            self.knowledge.roles.set_task(UnitTask.Reserved, harash_dt)
            self.knowledge.roles.set_task(UnitTask.Reserved, attack_dt)
            self.ninja_dt_tag = harash_dt.tag

        elif self.dt_push_started:
            harash_dt = self.ai.units.find_by_tag(self.ninja_dt_tag)
            if harash_dt is not None:
                enemy_workers = self.knowledge.known_enemy_units.of_type(
                    [UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE])
                if enemy_workers.exists:
                    target = enemy_workers.closest_to(harash_dt)
                    self.do(harash_dt.attack(target))
        return True

class DarkTemplarRush(KnowledgeBot):
    def __init__(self):
        super().__init__("Sharp Shadows")

    async def create_plan(self) -> BuildOrder:
        self.knowledge.building_solver.wall_type = 3  # WallType.ProtossMainZerg

        build_steps_buildings2 = [
            Step(RequiredUnitReady(UnitTypeId.GATEWAY, 1), GridBuilding(UnitTypeId.CYBERNETICSCORE, 1)),
            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), GridBuilding(UnitTypeId.TWILIGHTCOUNCIL, 1)),
            Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), GridBuilding(UnitTypeId.DARKSHRINE, 1)),
            ActTech(UpgradeId.BLINKTECH),
            ActTech(UpgradeId.CHARGE)
        ]

        build_steps_workers = [
            Step(None, ActBuilding(UnitTypeId.NEXUS, 1), RequiredUnitExists(UnitTypeId.NEXUS, 1)),

            # Build to 14 probes and stop until pylon is building
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), RequiredUnitExists(UnitTypeId.PROBE, 14)),
            Step(None, None, RequiredUnitExists(UnitTypeId.PYLON, 1)),

            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), RequiredUnitExists(UnitTypeId.PROBE, 16 + 3 + 3)),
            Step(RequireCustom(lambda k: self.knowledge.own_main_zone.minerals_running_low), ActExpand(2)),
            Step(None, ActUnit(UnitTypeId.PROBE, UnitTypeId.NEXUS), RequiredUnitExists(UnitTypeId.PROBE, 30)),
            GridBuilding(UnitTypeId.GATEWAY, 5),
            StepBuildGas(3),
            GridBuilding(UnitTypeId.GATEWAY, 6),
        ]

        build_steps_buildings = [
            Step(RequiredSupply(14), GridBuilding(UnitTypeId.PYLON, 1), RequiredUnitExists(UnitTypeId.PYLON, 1)),
            StepBuildGas(1, RequiredSupply(16)),
            Step(RequiredSupply(16), GridBuilding(UnitTypeId.GATEWAY, 1), RequiredTotalUnitExists([UnitTypeId.GATEWAY, UnitTypeId.WARPGATE], 1)),
            StepBuildGas(2),
            Step(RequiredSupply(21), GridBuilding(UnitTypeId.PYLON, 2), RequiredUnitExists(UnitTypeId.PYLON, 2)),
            GridBuilding(UnitTypeId.GATEWAY, 2),
            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1), ActTech(UpgradeId.WARPGATERESEARCH)),

            GridBuilding(UnitTypeId.GATEWAY, 3),
            AutoPylon()
        ]

        build_steps_units = [
            Step(None, ProtossUnit(UnitTypeId.DARKTEMPLAR, 4, priority=True), skip_until=RequiredUnitReady(UnitTypeId.DARKSHRINE, 1)),
            Step(RequiredUnitReady(UnitTypeId.GATEWAY, 1), ProtossUnit(UnitTypeId.ZEALOT, 1), RequiredTechReady(UpgradeId.WARPGATERESEARCH, 1)),
            Step(None, ProtossUnit(UnitTypeId.STALKER), None),
        ]
        build_steps_units2 = [
            Step(RequiredUnitExists(UnitTypeId.TWILIGHTCOUNCIL, 1), ProtossUnit(UnitTypeId.STALKER, 3), RequiredTechReady(UpgradeId.WARPGATERESEARCH, 1)),
            Step(RequiredMinerals(400), ProtossUnit(UnitTypeId.ZEALOT))
            ]

        build_steps_chrono = [
            Step(None, ChronoUnitProduction(UnitTypeId.PROBE, UnitTypeId.NEXUS),
                 skip=RequiredUnitExists(UnitTypeId.PROBE, 20, include_killed=True),
                 skip_until=RequiredUnitReady(UnitTypeId.PYLON)),
            ChronoAnyTech(0)
        ]

        build_order = BuildOrder([
            build_steps_buildings,
            build_steps_buildings2,
            build_steps_workers,
            build_steps_units,
            build_steps_units2,
            build_steps_chrono
        ])

        attack = PlanZoneAttack(20)
        attack.retreat_multiplier = 0.5  # All in

        tactics = [
            PlanCancelBuilding(),
            PlanZoneDefense(),
            RestorePower(),
            PlanDistributeWorkers(),
            DtPush(),
            PlanZoneGather(),
            attack,
            PlanFinishEnemy(),
        ]

        return BuildOrder([
            build_order,
            tactics
        ])


class LadderBot(DarkTemplarRush):
    @property
    def my_race(self):
        return Race.Protoss
