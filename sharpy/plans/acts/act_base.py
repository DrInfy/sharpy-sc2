import string
from abc import ABC, abstractmethod
from typing import List

import sc2
from sharpy.managers import UnitValue
from sharpy.managers import UnitCacheManager, PathingManager, GroupCombatManager, UnitRoleManager

from sc2 import AbilityId, Race, UnitTypeId
from sc2.client import Client
from sc2.position import Point2
from sc2.unit import Unit, UnitOrder
from sc2.unit_command import UnitCommand
from sc2.units import Units


build_commands = {
    # Protoss

    AbilityId.PROTOSSBUILD_NEXUS,
    AbilityId.PROTOSSBUILD_PYLON,
    AbilityId.PROTOSSBUILD_GATEWAY,
    AbilityId.PROTOSSBUILD_ASSIMILATOR,
    AbilityId.PROTOSSBUILD_CYBERNETICSCORE,
    AbilityId.PROTOSSBUILD_FORGE,
    AbilityId.PROTOSSBUILD_PHOTONCANNON,
    AbilityId.BUILD_SHIELDBATTERY,
    AbilityId.PROTOSSBUILD_STARGATE,
    AbilityId.PROTOSSBUILD_FLEETBEACON,
    AbilityId.PROTOSSBUILD_TWILIGHTCOUNCIL,
    AbilityId.PROTOSSBUILD_TEMPLARARCHIVE,
    AbilityId.PROTOSSBUILD_DARKSHRINE,
    AbilityId.PROTOSSBUILD_ROBOTICSFACILITY,
    AbilityId.PROTOSSBUILD_ROBOTICSBAY,

    # Terran
    AbilityId.TERRANBUILD_COMMANDCENTER,
    AbilityId.TERRANBUILD_SUPPLYDEPOT,
    AbilityId.TERRANBUILD_BARRACKS,
    AbilityId.TERRANBUILD_REFINERY,
    AbilityId.TERRANBUILD_ENGINEERINGBAY,
    AbilityId.TERRANBUILD_FACTORY,
    AbilityId.TERRANBUILD_ARMORY,
    AbilityId.TERRANBUILD_MISSILETURRET,
    AbilityId.TERRANBUILD_BUNKER,
    AbilityId.TERRANBUILD_SENSORTOWER,
    AbilityId.TERRANBUILD_GHOSTACADEMY,
    AbilityId.TERRANBUILD_STARPORT,
    AbilityId.TERRANBUILD_FUSIONCORE,

    # Zerg
    AbilityId.ZERGBUILD_BANELINGNEST,
    AbilityId.ZERGBUILD_EVOLUTIONCHAMBER,
    AbilityId.ZERGBUILD_EXTRACTOR,
    AbilityId.ZERGBUILD_HATCHERY,
    AbilityId.ZERGBUILD_HYDRALISKDEN,
    AbilityId.ZERGBUILD_INFESTATIONPIT,
    AbilityId.ZERGBUILD_NYDUSNETWORK,
    AbilityId.ZERGBUILD_ROACHWARREN,
    AbilityId.ZERGBUILD_SPAWNINGPOOL,
    AbilityId.ZERGBUILD_SPINECRAWLER,
    AbilityId.ZERGBUILD_SPIRE,
    AbilityId.ZERGBUILD_SPORECRAWLER,
    AbilityId.ZERGBUILD_ULTRALISKCAVERN,
}


class ActBase(ABC):
    knowledge: 'Knowledge'
    ai: sc2.BotAI
    cache: UnitCacheManager
    unit_values: UnitValue
    pather: PathingManager
    combat: GroupCombatManager
    roles: UnitRoleManager

    def __init__(self):
        _debug: bool = False

    @property
    def debug(self):
        return self._debug and self.knowledge.debug

    async def debug_draw(self):
        if self.debug:
            await self.debug_actions()

    async def debug_actions(self):
        pass

    def do(self, action: UnitCommand):
        self.knowledge.action_handler.action_made(action)
        self.ai.do(action)

    def allow_new_action(self, unit: Unit) -> bool:
        """
        Only use this check for critical orders that must not duplicated
        :param unit: unit that wants to make a new action
        :return: True if it allowed
        """
        return self.knowledge.action_handler.allow_action(unit)

    async def start(self, knowledge: 'Knowledge'):
        self.knowledge = knowledge
        self._debug = self.knowledge.get_boolean_setting(f"debug.{type(self).__name__}")
        self.ai = knowledge.ai
        self.cache = knowledge.unit_cache
        self.unit_values = knowledge.unit_values
        self._client: Client = self.ai._client
        self.pather = self.knowledge.pathing_manager
        self.combat = self.knowledge.combat_manager
        self.roles = self.knowledge.roles

    def print(self, msg: string, stats: bool = True):
        self.knowledge.print(msg, type(self).__name__, stats)

    @abstractmethod
    async def execute(self) -> bool:
        """Return True when the act is complete and execution can continue to the next act.
        Return False if you want to block execution and not continue to the next act."""
        pass

    def pending_build(self, unit_type: UnitTypeId) -> float:
        return self.ai.already_pending(unit_type)

    def pending_building_positions(self, unit_type: UnitTypeId) -> List[Point2]:
        """Returns positions of buildings of the specified type that have either been ordered to be built by a worker
        or are currently being built."""
        positions: List[Point2] = list()
        creation_ability: AbilityId = self.ai._game_data.units[unit_type.value].creation_ability

        # Workers ordered to build
        for worker in self.ai.workers:  # type: Unit
            for order in worker.orders:  # type: UnitOrder
                if order.ability.id == creation_ability.id:
                    p2: Point2 = Point2.from_proto(order.target)
                    positions.append(p2)

        # Already building structures
        # Avoid counting structures twice for Terran SCVs.
        if self.knowledge.my_race != Race.Terran:
            pending_buildings: List[Point2] = list(map(lambda structure: structure.position, self.cache.own(unit_type).structure.not_ready))
            positions.extend(pending_buildings)

        return positions

    def unit_pending_count(self, unit_type: UnitTypeId) -> float:
        return self.ai.already_pending(unit_type)

    def building_progress(self, pre_type: UnitTypeId):
        percentage = 0

        if pre_type == UnitTypeId.SUPPLYDEPOT:
            types = [UnitTypeId.SUPPLYDEPOTDROP, UnitTypeId.SUPPLYDEPOTDROP, UnitTypeId.SUPPLYDEPOTLOWERED]
        else:
            types = pre_type

        for unit in self.cache.own(types):
            if unit.is_ready:
                return 0
            percentage = max(percentage, unit.build_progress)

        if percentage == 0:
            return 1000

        return self.unit_values.build_time(pre_type) * (1 - percentage)

    def has_build_order(self, worker: Unit):
        if worker.orders:
            for orders in worker.orders:
                if orders.ability.id in build_commands:
                    return True
        return False

    def get_count(self, unit_type: UnitTypeId,
                  include_pending=True,
                  include_killed=False,
                  include_not_ready: bool = True) -> int:
        """Calculates how many buildings there are already, including pending structures."""
        count = 0

        type_count = self.cache.own(unit_type)

        if include_not_ready and include_pending:
            count += self.unit_pending_count(unit_type)
            count += type_count.ready.amount
        elif include_not_ready and not include_pending:
            count += type_count.amount
        elif not include_not_ready and include_pending:
            count += self.unit_pending_count(unit_type)
            count += type_count.amount - type_count.not_ready.amount
        else:
            # Only and only ready
            count += type_count.ready.amount

        count = self.related_count(count, unit_type)

        if include_killed:
            count += self.knowledge.lost_units_manager.own_lost_type(unit_type)

        return count

    def related_count(self, count, unit_type):
        if unit_type == UnitTypeId.SPIRE:
            count += self.cache.own(UnitTypeId.GREATERSPIRE).amount
        if unit_type == UnitTypeId.WARPGATE:
            count += self.cache.own(UnitTypeId.GATEWAY).amount
        if unit_type == UnitTypeId.WARPPRISM:
            count += self.cache.own(UnitTypeId.WARPPRISMPHASING).amount
        if unit_type == UnitTypeId.LAIR:
            count += self.cache.own(UnitTypeId.HIVE).amount
        if unit_type == UnitTypeId.GATEWAY:
            count += self.cache.own(UnitTypeId.WARPGATE).amount
        if unit_type == UnitTypeId.COMMANDCENTER:
            count += self.cache.own(UnitTypeId.ORBITALCOMMAND).amount
            count += self.cache.own(UnitTypeId.PLANETARYFORTRESS).amount
        if unit_type == UnitTypeId.HATCHERY:
            count += self.cache.own(UnitTypeId.LAIR).amount
            count += self.cache.own(UnitTypeId.HIVE).amount
        if unit_type == UnitTypeId.SUPPLYDEPOT:
            count += self.cache.own(UnitTypeId.SUPPLYDEPOTDROP).amount
            count += self.cache.own(UnitTypeId.SUPPLYDEPOTLOWERED).amount
        if unit_type == UnitTypeId.SIEGETANK:
            count += self.cache.own(UnitTypeId.SIEGETANKSIEGED).amount
        if unit_type == UnitTypeId.VIKINGFIGHTER:
            count += self.cache.own(UnitTypeId.VIKINGASSAULT).amount
        return count
