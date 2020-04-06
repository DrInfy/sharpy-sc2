import logging
import string
from configparser import ConfigParser
from typing import Set, List, Optional, Dict, Callable

import sc2
from sharpy.general.zone import Zone
from sharpy.events import UnitDestroyedEvent
from sharpy.managers import *
from sharpy.managers.enemy_units_manager import EnemyUnitsManager
from sharpy.mapping.heat_map import HeatMap
from sharpy.mapping.map import MapInfo
from sharpy.general.extended_ramp import ExtendedRamp
from sc2 import Race
from sc2.constants import *
from sc2.data import Result
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

root_logger = logging.getLogger()


class Knowledge:
    def __init__(self):
        self.ai: sc2.BotAI = None
        self.config: ConfigParser = None
        self._debug: bool = False

        self.iteration = 0

        self.supply_blocked = False

        self.my_worker_type: UnitTypeId = None
        self.enemy_worker_type: Optional[UnitTypeId] = None

        # Information about units in game
        self.unit_values: UnitValue = UnitValue()

        self.rush_distance = 0

        self._all_own: Units = None


        # Base building related
        self.reserved_minerals = 0
        self.reserved_gas = 0
        self.expanding_to: Zone = None

        # Event listeners
        self._on_unit_destroyed_listeners: List[Callable] = list()

        # Managers
        self.unit_cache: UnitCacheManager = UnitCacheManager()
        self.zone_manager: ZoneManager = ZoneManager()
        self.enemy_units_manager: EnemyUnitsManager = EnemyUnitsManager()
        self.cooldown_manager: CooldownManager = CooldownManager()
        self.building_solver = BuildingSolver()
        self.income_calculator = IncomeCalculator()
        self.roles: UnitRoleManager = UnitRoleManager()
        self.build_detector: BuildDetector = BuildDetector()
        self.pathing_manager: PathingManager = PathingManager()
        self.enemy_army_predicter = EnemyArmyPredicter()
        self.lost_units_manager: LostUnitsManager = LostUnitsManager()
        self.game_analyzer: GameAnalyzer = GameAnalyzer()
        self.previous_units_manager: PreviousUnitsManager = PreviousUnitsManager()
        self.data_manager: DataManager = DataManager()
        self.combat_manager: GroupCombatManager = GroupCombatManager()
        self.chat_manager: ChatManager = ChatManager()
        self.memory_manager: MemoryManager = MemoryManager()
        self.action_handler: ActionHandler = ActionHandler()

        self.managers: List[ManagerBase] = [
            self.unit_values,
            self.unit_cache,
            self.action_handler,
            self.pathing_manager,
            self.zone_manager,
            self.enemy_units_manager,
            self.cooldown_manager,
            self.building_solver,
            self.income_calculator,
            self.roles,
            self.build_detector,
            self.enemy_army_predicter,
            self.lost_units_manager,
            self.game_analyzer,
            self.combat_manager,
            self.chat_manager,
            self.previous_units_manager,
            self.data_manager,
            self.memory_manager,
        ]

    # noinspection PyAttributeOutsideInit
    def pre_start(self, ai: sc2.BotAI):
        self.ai: sc2.BotAI = ai
        self._all_own: Units = Units([], self.ai)
        self.config: ConfigParser = self.ai.config
        self.logger = sc2.main.logger
        self.is_chat_allowed = self.config["general"].getboolean("chat")
        self._debug = self.config["general"].getboolean("debug")

        self.my_race: Race = self.ai.race
        self.enemy_race: Race = self.ai.enemy_race
        self.enemy_worker_type = self.unit_values.get_worker_type(self.enemy_race)

        self.map = MapInfo(self)
        self.close_gates = self.enemy_race == Race.Zerg

        # Cached ai fields:
        self._known_enemy_structures: Units = self.ai.enemy_structures
        self._known_enemy_units: Units = self.ai.enemy_units + self.ai.enemy_structures
        self._known_enemy_units_mobile: Units = self.ai.enemy_units
        self._known_enemy_units_workers: Units = Units([], self.ai)

        self.heat_map = HeatMap(self.ai, self)

        self.my_worker_type = self.unit_values.get_worker_type(self.my_race)

    def get_str_setting(self, key: str) -> str:
        """
        Returns a string setting from config.ini matching the key.

        :param key: Key of the setting, eg. "builds.edge_protoss" for "edge_protoss" setting under [builds].
        """
        key = key.split('.')
        return self.config[key[0]].get(key[1])

    def get_int_setting(self, key: str) -> int:
        """
        Returns a boolean setting from config.ini matching the key.

        :param key: Key of the setting, eg. "gameplay.disruptor_max_count" for "disruptor_max_count" setting under [gameplay].
        """
        key = key.split('.')
        return self.config[key[0]].getint(key[1])

    def get_boolean_setting(self, key: str) -> str:
        """
        Returns a boolean setting from config.ini matching the key.

        :param key: Key of the setting, eg. "general.chat" for "chat" setting under [general].
        """
        key = key.split('.')
        return self.config[key[0]].getboolean(key[1])

    @property
    def available_mineral(self) -> int:
        return self.ai.minerals - self.reserved_minerals

    @property
    def available_gas(self) -> int:
        return self.ai.vespene - self.reserved_gas

    @property
    def gate_keeper_position(self) -> Optional[Point2]:
        return self.building_solver.zealot_position

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def all_own(self) -> Units:
        return self._all_own

    @property
    def known_enemy_structures(self) -> Units:
        return self._known_enemy_structures

    @property
    def known_enemy_units(self) -> Units:
        """Returns all known enemy units and structures."""
        return self._known_enemy_units

    @property
    def known_enemy_units_mobile(self) -> Units:
        return self._known_enemy_units_mobile

    @property
    def known_enemy_workers(self) -> Units:
        return self._known_enemy_units_workers

    @property
    def possible_rush_detected(self) -> bool:
        """ True if scouting indicates that the enemy is preparing an early rush. """
        return self.build_detector.rush_detected

    @property
    def base_ramp(self) -> ExtendedRamp:
        """Own start location ramp. Note that ai.main_base_ramp is incorrect in several maps, so scrap that."""
        return self.expansion_zones[0].ramp

    @property
    def enemy_base_ramp(self) -> ExtendedRamp:
        """Enemy start location ramp, based on our best case of the enemy start location."""
        return self.expansion_zones[-1].ramp

    @property
    def natural_wall(self) -> bool:
        natural = self.zone_manager.expansion_zones[1]
        return natural.is_ours and natural.our_wall()

    async def start(self):
        for manager in self.managers:
            await manager.start(self)

        self.gather_point = self.base_ramp.top_center.towards(self.base_ramp.bottom_center, -4)
        start = self.base_ramp.top_center
        end = self.enemy_base_ramp.top_center
        self.rush_distance = await self.ai._client.query_pathing(start, end)
        self._print(f"rush distance: {self.rush_distance}", stats=False)

    async def update(self, iteration: int):
        if self.close_gates:
            lings = self.enemy_units_manager.unit_count(UnitTypeId.ZERGLING)
            if self.enemy_units_manager.unit_count(UnitTypeId.ROACH) > lings\
                    or self.enemy_units_manager.unit_count(UnitTypeId.HYDRALISK) > lings:
                self.close_gates = False

        self._all_own: Units = self.ai.units + self.ai.structures
        memory_units = self.memory_manager.ghost_units
        self._known_enemy_structures: Units = self.ai.enemy_structures.filter(
            lambda u: u.is_structure and u.type_id not in self.unit_values.not_really_structure)
        self._known_enemy_units: Units = self.ai.enemy_units + self.ai.enemy_structures + memory_units
        self._known_enemy_units_mobile: Units = self.ai.enemy_units + memory_units

        self._known_enemy_units_workers: Units =\
            Units(self._known_enemy_units_mobile.of_type([UnitTypeId.SCV, UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.MULE]),
                  self.ai)

        self.iteration = iteration

        for manager in self.managers:
            await manager.update()

        if not self.supply_blocked and self.ai.supply_left == 0:
            self.supply_blocked = True
            self.print(f"Started", "SupplyBlock")
        elif self.supply_blocked and self.ai.supply_left > 0:
            self.supply_blocked = False
            self.print(f"Ended", "SupplyBlock")

        self._find_gather_point()

        # Reserved resources are reseted each iteration
        self.expanding_to = None
        self.reserved_minerals = 0
        self.reserved_gas = 0
        self.heat_map.update()
        self.update_enemy_random()

    def update_enemy_random(self):
        if self.enemy_race == Race.Random:
            if self._known_enemy_units_workers(UnitTypeId.SCV).exists:
                self.enemy_race = Race.Terran
            if self._known_enemy_units_workers(UnitTypeId.DRONE).exists:
                self.enemy_race = Race.Zerg
            if self._known_enemy_units_workers(UnitTypeId.PROBE).exists:
                self.enemy_race = Race.Protoss

            self.enemy_worker_type = self.unit_values.get_worker_type(self.enemy_race)

    def reserve(self, minerals: int, gas: int):
        self.reserved_minerals += minerals
        self.reserved_gas += gas

    def reserve_costs(self, item_id: sc2.Union[UnitTypeId, UpgradeId, AbilityId]):
        if isinstance(item_id, UnitTypeId):
            unit = self.ai._game_data.units[item_id.value]
            cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)
        elif isinstance(item_id, UpgradeId):
            cost = self.ai._game_data.upgrades[item_id.value].cost
        else:
            cost = self.ai._game_data.calculate_ability_cost(item_id)
        self.reserve(cost.minerals, cost.vespene)

    def can_afford(self, item_id: sc2.Union[UnitTypeId, UpgradeId, AbilityId], check_supply_cost: bool = True) -> bool:
        """Tests if the player has enough resources to build a unit or cast an ability even after reservations."""
        enough_supply = True
        if isinstance(item_id, UnitTypeId):
            unit = self.ai._game_data.units[item_id.value]
            cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)
            if check_supply_cost:
                enough_supply = self.ai.can_feed(item_id)
        elif isinstance(item_id, UpgradeId):
            cost = self.ai._game_data.upgrades[item_id.value].cost
        else:
            cost = self.ai._game_data.calculate_ability_cost(item_id)
        minerals = self.ai.minerals - self.reserved_minerals
        gas = self.ai.vespene - self.reserved_gas
        return cost.minerals <= minerals and cost.vespene <= max(0,gas) and enough_supply

    def should_attack(self, unit: Unit):
        """Returns boolean whether unit should participate in an attack. Ignores structures, workers and other non attacking types."""
        if unit.type_id in self.unit_values.combat_ignore:
            return False
        if self.my_race == Race.Zerg and unit.type_id == UnitTypeId.QUEEN:
            return False
        if unit.type_id == UnitTypeId.INTERCEPTOR or unit.type_id == UnitTypeId.ADEPTPHASESHIFT or unit.type_id == UnitTypeId.MULE:
            return False
        return not unit.is_structure and self.my_worker_type != unit.type_id

    def building_going_down(self, building: Unit) -> bool:
        """Returns boolean indicating whether a building is low on health and under attack."""
        if building.tag in self.previous_units_manager.previous_units:
            previous_building = self.previous_units_manager.previous_units[building.tag]
            health = building.health
            compare_health = max(70, building.health_max * 0.09)
            if health < previous_building.health < compare_health:
                return True
        return False

    @property
    def enemy_expansions_dict(self) -> Dict[Point2, Unit]:
        """Dictionary of known expansion locations that have an enemy townhall present."""

        # This is basically copy pasted from BotAI.owned_expansions
        expansions = {}

        for exp_loc in self.ai.expansion_locations:
            def is_near_to_expansion(th: Unit):
                return th.position.distance_to(exp_loc) < sc2.BotAI.EXPANSION_GAP_THRESHOLD

            townhall = next((x for x in self.enemy_townhalls if is_near_to_expansion(x)), None)
            if townhall:
                expansions[exp_loc] = townhall

        return expansions

    def building_started_before(self, type_id: UnitTypeId, start_time_ceiling: int) -> bool:
        """Returns true if a building of type type_id has been started before start_time_ceiling seconds."""
        for unit in self.known_enemy_structures(type_id):  # type: Unit
            # fixme: for completed buildings this will report a time later than the actual start_time.
            # not fatal, but may be misleading.
            start_time = self.unit_values.building_start_time(self.ai.time, unit.type_id, unit.build_progress)
            if start_time is not None and start_time < start_time_ceiling:
                return True

        return False

    @property
    def enemy_townhalls(self):
        """Returns all known enemy townhalls, ie. Command Centers, Nexuses, Hatcheries,
        or one of their upgraded versions."""
        return self.known_enemy_structures.filter(self.unit_values.is_townhall)

    #
    # Zones and enemy start
    #

    @property
    def likely_enemy_start_location(self) -> Optional[Point2]:
        return self.zone_manager.expansion_zones[-1].center_location

    @property
    def enemy_start_location_found(self) -> bool:
        """Returns true if enemy start location has (probably) been found."""
        return self.zone_manager.enemy_start_location_found

    @property
    def unscouted_zones(self) -> List[Zone]:
        """Returns a list of all zones that have not been scouted."""
        unscouted = [z for z in self.zone_manager.all_zones if not z.is_scouted_at_least_once]
        return unscouted

    @property
    def expansion_zones(self) -> List[Zone]:
        return self.zone_manager.expansion_zones

    @property
    def enemy_expansion_zones(self) -> List[Zone]:
        return self.zone_manager.enemy_expansion_zones

    @property
    def our_zones(self) -> List[Zone]:
        """Returns all of our own zones."""
        ours = [z for z in self.zone_manager.all_zones if z.is_ours]
        return ours

    @property
    def our_zones_with_minerals(self) -> List[Zone]:
        """Returns all of our zones that have minerals."""
        filtered = filter(lambda z: z.our_townhall and z.has_minerals, self.our_zones)
        return list(filtered)

    @property
    def own_main_zone(self) -> Zone:
        """Returns our own main zone. If we have lost our base at start location, it will be the
        next safe expansion."""
        return self.zone_manager.own_main_zone

    @property
    def enemy_main_zone(self) -> Zone:
        """ Returns enemy main / start zone."""
        return self.zone_manager.enemy_main_zone

    @property
    def enemy_start_location(self) -> Optional[Point2]:
        """Returns the enemy start location, if found."""
        return self.zone_manager.enemy_start_location

    #
    # BotAI event handlers
    #

    async def on_unit_destroyed(self, unit_tag: int):
        # BotAI._units_previous_map[unit_tag] does not contain enemies. :(
        if unit_tag in self.previous_units_manager.previous_units:
            unit = self.previous_units_manager.previous_units[unit_tag]
        else:
            unit = None
            self._print(f"Unknown unit destroyed: {unit_tag}", log_level=logging.DEBUG)

        self.fire_event(self._on_unit_destroyed_listeners, UnitDestroyedEvent(unit_tag, unit))

    async def on_unit_created(self, unit: Unit):
        # This does not seem to be useful, because the same tag is "created" many many times in a match.
        # It may be a bug with our own bot, because others do not seem to be having the problem.
        # if self.knowledge is not None:
        #     self.knowledge._print(f"{unit.type_id} created, position {unit.position} tag {unit.tag}")
        pass

    async def on_building_construction_started(self, unit: Unit):
        self._print(f"Started {unit.type_id.name} at {unit.position}"
        )

    async def on_building_construction_complete(self, unit: Unit):
        self._print(f"Completed {unit.type_id.name} at {unit.position}"
        )

    async def on_end(self, game_result: Result):
        self._print(f"Result: {game_result.name}", stats=False)
        self._print(f"Duration: {self.ai.time_formatted}", stats=False)

        try:
            step_time_min = round(self.ai.step_time[0])
            self._print(f"Step time min: {step_time_min}", stats=False)
        except OverflowError:
            # step_time_min is infinite at the start and can cause an unnecessary exception.
            pass

        step_time_avg = round(self.ai.step_time[1])
        self._print(f"Step time avg: {step_time_avg}", stats=False)

        step_time_max = round(self.ai.step_time[2])
        self._print(f"Step time max: {step_time_max}", stats=False)

        for manager in self.managers:
            await manager.on_end(game_result)

# region Knowledge event handlers

    # todo: if this is useful, it should be refactored as a more general solution

    def register_on_unit_destroyed_listener(self, func: Callable[[UnitDestroyedEvent], None]):
        assert isinstance(func, Callable)
        self._on_unit_destroyed_listeners.append(func)

    def unregister_on_unit_destroyed_listener(self, func):
        raise NotImplemented()

    @staticmethod
    def fire_event(listeners, event):
        for listener in listeners:
            listener(event)

# endregion

    #
    # Printing
    #

    def _print(self, message: string, stats: bool = True, log_level=logging.INFO):
        """Private print method for Knowledge class."""
        self.print(message, tag=type(self).__name__, stats=stats, log_level=log_level)

    def print(self, message: string, tag: string = None, stats: bool = True, log_level=logging.INFO):
        """
        Prints a message to log.

        :param message: The message to print.
        :param tag: An optional tag, which can be used to indicate the logging component.
        :param stats: When true, stats such as time, minerals, gas, and supply are added to the log message.
        :param log_level: Optional logging level. Default is INFO.
        """
        if tag is not None:
            debug_log = self.config["debug_log"]
            enabled = debug_log.getboolean(tag, fallback=True)
            if not enabled:
                return

        if tag is not None:
            message = f"[{tag}] {message}"

        if stats:
            last_step_time = round(self.ai.step_time[3])

            message = f"{self.ai.time_formatted.rjust(5)} {str(last_step_time).rjust(4)}ms " \
                f"{str(self.ai.minerals).rjust(4)}M {str(self.ai.vespene).rjust(4)}G " \
                f"{str(self.ai.supply_used).rjust(3)}/{str(self.ai.supply_cap).rjust(3)}U {message}"

        # noinspection PyUnresolvedReferences
        if not self.ai.run_custom or self.ai.player_id == 1 or self.ai.realtime:
            message = f"[EDGE] {message}"
        elif not self.config["general"].getboolean("frozen_log") and tag != "Build":
            return  # No print

        if self.logger.hasHandlers():
            # Write to the competition site log
            self.logger.log(log_level, message)
        else:
            # Write to our own log configured in run_custom.py
            logging.log(log_level, message)

    def _find_gather_point(self):
        self.gather_point = self.base_ramp.top_center.towards(self.base_ramp.bottom_center, -4)
        start = 1
        if self.map.safe_first_expand:
            start = 2

        for i in range(start, len(self.zone_manager.expansion_zones)):
            zone = self.zone_manager.expansion_zones[i]
            if zone.expanding_to:
                self.gather_point = zone.gather_point
            elif zone.is_ours:
                if len(self.zone_manager.gather_points) > i:
                    self.gather_point = self.zone_manager.expansion_zones[self.zone_manager.gather_points[i]].gather_point

    def get_z(self, point: Point2):
        return self.terrain_to_z_height(self.ai.get_terrain_height(point))

    def terrain_to_z_height(self, h):
        """Gets correct z from versions 4.9.0+"""
        return -16 + 32 * h / 255

    async def post_update(self):
        for manager in self.managers:
            await manager.post_update()

        # if self.debug:
        #     await self.ai._client.send_debug()
