import logging
import string
from configparser import ConfigParser
from typing import List, Optional, Callable, Type, Union

from sc2.data import Race, Result
from sharpy.events import UnitDestroyedEvent
from sharpy.interfaces.data_manager import IDataManager
from sharpy.managers.core import *
from sharpy.interfaces import (
    ILagHandler,
    IUnitCache,
    IUnitValues,
    ICombatManager,
    ILogManager,
    IZoneManager,
    IPostStart,
    IPreviousUnitsManager,
)
from sc2.constants import *
from sc2.position import Point2
from typing import TYPE_CHECKING, TypeVar

from sharpy.managers.core import LogManager

if TYPE_CHECKING:
    from sharpy.knowledges import SkeletonBot


root_logger = logging.getLogger()
TManager = TypeVar("TManager")


class Knowledge:
    my_worker_type: UnitTypeId

    def __init__(self):
        self.ai: "SkeletonBot" = None
        self.config: ConfigParser = None
        self._debug: bool = False
        self.is_chat_allowed: bool = False

        self.started = False
        self.action_handler: ActionManager = ActionManager()
        self.version_manager: VersionManager = VersionManager()
        self.managers: List[ManagerBase] = []

        self.iteration: int = 0
        self.reserved_minerals: int = 0
        self.reserved_gas: int = 0
        self.log_manager: ILogManager = LogManager()
        # TODO: Remove references to these managers
        self.lag_handler: Optional[ILagHandler] = None
        self.unit_values: Optional[IUnitValues] = None
        self.pathing_manager: Optional[PathingManager] = None
        self.zone_manager: Optional[ZoneManager] = None
        self.cooldown_manager: Optional[CooldownManager] = None
        self.roles: Optional[UnitRoleManager] = None
        self.combat_manager: Optional[ICombatManager] = None
        self.previous_units_manager: Optional[IPreviousUnitsManager] = None

        # Event listeners
        self._on_unit_destroyed_listeners: List[Callable] = list()

    @property
    def debug(self) -> bool:
        return self._debug

    @property
    def my_race(self):
        return self.ai.race

    @property
    def enemy_race(self) -> Race:
        """ Enemy random race gets updated when the bot meets one of the enemy units. """
        return self.ai.enemy_race

    @property
    def unit_cache(self) -> Optional[IUnitCache]:
        return self.get_manager(IUnitCache)

    def pre_start(self, ai: "SkeletonBot", additional_managers: Optional[List[ManagerBase]]):
        # assert isinstance(ai, BotAI)
        self.ai: "SkeletonBot" = ai
        self._set_managers(additional_managers)
        self.config: ConfigParser = self.ai.config
        self.is_chat_allowed = self.config["general"].getboolean("chat")
        self._debug = self.config["general"].getboolean("debug")
        self.my_worker_type = UnitValue.get_worker_type(self.my_race)

        if self.ai.start_location is None:
            if self.ai.structures:
                self.ai.game_info.player_start_location = self.ai.structures.center
            elif self.ai.structures:
                self.ai.game_info.player_start_location = self.ai.units.center
            else:
                self.ai.game_info.player_start_location = self.ai.game_info.map_center

            if self.ai.enemy_structures:
                self.ai.game_info.start_locations = [self.ai.enemy_structures.center]
            else:
                self.ai.game_info.start_locations = [self.ai.game_info.map_center]

    def _set_managers(self, additional_managers: Optional[List[ManagerBase]]):
        """
        Sets managers to be updated.
        This is not intended to be used outside of Knowledge.
        Use KnowledgeBot.configure_managers to configure your managers.

        @param additional_managers: Additional list of custom managers
        """
        self.managers: List[ManagerBase] = [
            self.log_manager,
            self.version_manager,
            self.action_handler,
        ]

        if additional_managers:
            self.managers.extend(additional_managers)

    def get_manager(self, manager_type: Type[TManager]) -> Optional[TManager]:
        """
        Get manager by its type. Because the implementation can pretty slow, it is recommended to
        fetch the required manager types in Component `start` in order to not slow the bot down.

        @param manager_type: type of manager to be requested. i.e. `DataManager`
        @return: Manager of requested type, if one is found.
        """
        for manager in self.managers:
            if issubclass(type(manager), manager_type):
                return manager

    def get_required_manager(self, manager_type: Type[TManager]) -> TManager:
        """
        Get manager by its type. Because the implementation can pretty slow, it is recommended to
        fetch the required manager types in Component `start` in order to not slow the bot down.
        Throws an except if no manager if the specified type is found.

        @param manager_type: type of manager to be requested. i.e. `DataManager`
        @return: Manager of requested type
        """
        manager = self.get_manager(manager_type)
        if not manager:
            raise KeyError(manager_type)
        return manager

    async def start(self):
        # TODO: Remove these
        self.unit_values = self.get_manager(IUnitValues)
        self.lag_handler = self.get_manager(ILagHandler)
        self.pathing_manager = self.get_manager(PathingManager)
        self.zone_manager = self.get_manager(IZoneManager)
        self.cooldown_manager = self.get_manager(CooldownManager)
        self.roles = self.get_manager(UnitRoleManager)
        self.combat_manager = self.get_manager(ICombatManager)
        self.data_manager = self.get_manager(IDataManager)
        self.previous_units_manager = self.get_manager(IPreviousUnitsManager)

        for manager in self.managers:
            await manager.start(self)

        for manager in self.managers:
            if isinstance(manager, IPostStart):
                await manager.post_start()

        self.started = True

    async def update(self, iteration: int):
        self.iteration = iteration
        self.reserved_minerals = 0
        self.reserved_gas = 0

        for manager in self.managers:
            await manager.update()

    async def post_update(self):
        for manager in self.managers:
            await manager.post_update()

    def step_took(self, ns_step: float):
        """ Time taken in nanosecond for the current step to run. """
        if self.lag_handler:
            ms_step = ns_step / 1000 / 1000
            self.lag_handler.step_took(ms_step)

    @property
    def available_mineral(self) -> int:
        return self.ai.minerals - self.reserved_minerals

    @property
    def available_gas(self) -> int:
        return self.ai.vespene - self.reserved_gas

    def reserve(self, minerals: int, gas: int):
        self.reserved_minerals += minerals
        self.reserved_gas += gas

    def reserve_costs(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId]):
        if isinstance(item_id, UnitTypeId):
            unit = self.ai._game_data.units[item_id.value]
            cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)
        elif isinstance(item_id, UpgradeId):
            cost = self.ai._game_data.upgrades[item_id.value].cost
        else:
            cost = self.ai._game_data.calculate_ability_cost(item_id)
        self.reserve(cost.minerals, cost.vespene)

    def can_afford(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId], check_supply_cost: bool = True) -> bool:
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
        return cost.minerals <= minerals and cost.vespene <= max(0, gas) and enough_supply

    def print(self, message: string, tag: string = None, stats: bool = True, log_level=logging.INFO):
        """
        Prints a message to log.

        :param message: The message to print.
        :param tag: An optional tag, which can be used to indicate the logging component.
        :param stats: When true, stats such as time, minerals, gas, and supply are added to the log message.
        :param log_level: Optional logging level. Default is INFO.
        """
        self.log_manager.print(message, tag, stats, log_level)

    # region Knowledge event handlers

    async def on_unit_destroyed(self, unit_tag: int):
        # BotAI._units_previous_map[unit_tag] does not contain enemies. :(
        if self.previous_units_manager:
            unit = self.previous_units_manager.last_unit(unit_tag)
            if unit:
                self.fire_event(self._on_unit_destroyed_listeners, UnitDestroyedEvent(unit_tag, unit))
            else:
                self.print(f"Unknown unit destroyed: {unit_tag}", log_level=logging.DEBUG)

    # todo: if this is useful, it should be refactored as a more general solution

    def register_on_unit_destroyed_listener(self, func: Callable[[UnitDestroyedEvent], None]):
        assert isinstance(func, Callable)
        if self.previous_units_manager is None:
            raise Exception("Previous units manager needs the be set to register for the unit destroyed event")
        self._on_unit_destroyed_listeners.append(func)

    def unregister_on_unit_destroyed_listener(self, func):
        self._on_unit_destroyed_listeners.remove(func)

    @staticmethod
    def fire_event(listeners, event):
        for listener in listeners:
            listener(event)

    async def on_end(self, game_result: Result):
        self.print(f"Result: {game_result.name}", stats=False)
        self.print(f"Duration: {self.ai.time_formatted}", stats=False)

        try:
            step_time_min = round(self.ai.step_time[0])
            self.print(f"Step time min: {step_time_min}", stats=False)
        except OverflowError:
            # step_time_min is infinite at the start and can cause an unnecessary exception.
            pass

        step_time_avg = round(self.ai.step_time[1])
        self.print(f"Step time avg: {step_time_avg}", stats=False)

        step_time_max = round(self.ai.step_time[2])
        self.print(f"Step time max: {step_time_max}", stats=False)

        for manager in self.managers:
            await manager.on_end(game_result)

    # endregion

    # region Settings

    def get_str_setting(self, key: str) -> str:
        """
        Returns a string setting from config.ini matching the key.

        :param key: Key of the setting, eg. "builds.edge_protoss" for "edge_protoss" setting under [builds].
        """
        key = key.split(".")
        return self.config[key[0]].get(key[1])

    def get_int_setting(self, key: str) -> int:
        """
        Returns a boolean setting from config.ini matching the key.

        :param key: Key of the setting, eg. "gameplay.disruptor_max_count" for "disruptor_max_count" setting under [gameplay].
        """
        key = key.split(".")
        return self.config[key[0]].getint(key[1])

    def get_boolean_setting(self, key: str) -> str:
        """
        Returns a boolean setting from config.ini matching the key.

        :param key: Key of the setting, eg. "general.chat" for "chat" setting under [general].
        """
        key = key.split(".")
        return self.config[key[0]].getboolean(key[1])

    # endregion

    # region Map Height

    def get_z(self, point: Point2):
        return self.terrain_to_z_height(self.ai.get_terrain_height(point))

    def terrain_to_z_height(self, h):
        """Gets correct z from versions 4.9.0+"""
        return -16 + 32 * h / 255

    def z_height_to_terrain(self, z):
        """Gets correct height from versions 4.9.0+"""
        h = (z + 16) / 32 * 255
        return h

    # endregion
