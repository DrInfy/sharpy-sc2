import logging
import sys
import time

from sc2.bot_ai import BotAI
from sc2.constants import abilityid_to_unittypeid
from sc2.data import Result
from sc2.game_data import Cost
from sc2.ids.unit_typeid import UnitTypeId
from sc2.unit_command import UnitCommand
from sc2.units import Units
from config import get_config, get_version
from abc import abstractmethod, ABC
from typing import TYPE_CHECKING, Optional, List
from sharpy.knowledges.knowledge import Knowledge


if TYPE_CHECKING:
    from sharpy.managers.core import ManagerBase
    from sc2.unit import Unit


class SkeletonBot(BotAI, ABC):
    def __init__(self, name: str):
        self.knowledge = Knowledge()
        self.name = name
        self.config = get_config()
        # This is needed to know whether this is a custom run or game created by ladder manager
        self.run_custom = False
        self.realtime_worker = True
        self.realtime_split = True

        self.last_game_loop = -1

        self.distance_calculation_method = 0
        self.unit_command_uses_self_do = False
        # In general it is better to fail fast and early in order to fix things.
        self.crash_on_except = True

    async def on_start(self):
        """Allows initializing the bot when the game data is available."""
        self.knowledge.pre_start(self, self.configure_managers())
        await self.knowledge.start()

    @abstractmethod
    def configure_managers(self) -> Optional[List["ManagerBase"]]:
        """
        Override this for custom manager usage.
        Use this to override managers in knowledge
        @return: Optional list of new managers
        """
        pass

    async def on_step(self, iteration):
        try:
            if not self.realtime and self.last_game_loop == self.state.game_loop:
                self.realtime = True
                self.client.game_step = 1
                return

            self.last_game_loop = self.state.game_loop

            ns_step = time.perf_counter_ns()
            await self.knowledge.update(iteration)
            await self.execute()
            # await self.pre_step_execute()
            # await self.plan.execute()

            await self.knowledge.post_update()

            # if self.knowledge.debug:
            #     await self.plan.debug_draw()

            ns_step = time.perf_counter_ns() - ns_step
            self.knowledge.step_took(ns_step)

        except:  # noqa, catch all exceptions
            e = sys.exc_info()[0]
            logging.exception(e)

            if self.crash_on_except:
                # This crashes the bot and causes it to lose the match.
                raise

    async def execute(self):
        """
        Override this for your custom custom code after managers have updated their code
        @return: None
        """
        pass

    async def on_before_start(self):
        """
        Override this in your bot class. This function is called before "on_start"
        and before expansion locations are calculated.
        Not all data is available yet.
        """

        # Start building first worker before doing any heavy calculations
        # This is only needed for real time, but we don't really know whether the game is real time or not.
        await self.start_first_worker()
        await self.split_workers()

        # Commit and clear bot actions
        if self.actions:
            await self._do_actions(self.actions)
            self.actions.clear()

        self.client.game_step = int(self.config["general"]["game_step_size"])

    async def split_workers(self):
        if self.realtime_split:
            # Split workers
            mfs = self.mineral_field.closer_than(10, self.townhalls.first.position)
            workers = Units(self.workers, self)

            for mf in mfs:  # type: Unit
                if workers:
                    worker = workers.closest_to(mf)
                    worker.gather(mf)
                    workers.remove(worker)

            for w in workers:  # type: Unit
                w.gather(mfs.closest_to(w))

    async def start_first_worker(self):
        if self.townhalls and self.realtime_worker:
            townhall = self.townhalls.first
            if townhall.type_id == UnitTypeId.COMMANDCENTER:
                townhall.train(UnitTypeId.SCV)
            if townhall.type_id == UnitTypeId.NEXUS:
                townhall.train(UnitTypeId.PROBE)
            if townhall.type_id == UnitTypeId.HATCHERY:
                self.units(UnitTypeId.LARVA).first.train(UnitTypeId.DRONE)

    async def on_unit_destroyed(self, unit_tag: int):
        await self.knowledge.on_unit_destroyed(unit_tag)

    async def on_end(self, game_result: Result):
        await self.knowledge.on_end(game_result)

    def do(
        self,
        action: UnitCommand,
        subtract_cost: bool = False,
        subtract_supply: bool = False,
        can_afford_check: bool = False,
        ignore_warning: bool = False,
    ) -> bool:
        """ Adds a unit action to the 'self.actions' list which is then executed at the end of the frame.

        Training a unit::

            # Train an SCV from a random idle command center
            cc = self.townhalls.idle.random_or(None)
            # self.townhalls can be empty or there are no idle townhalls
            if cc and self.can_afford(UnitTypeId.SCV):
                cc.train(UnitTypeId.SCV)

        Building a building::

            # Building a barracks at the main ramp, requires 150 minerals and a depot
            worker = self.workers.random_or(None)
            barracks_placement_position = self.main_base_ramp.barracks_correct_placement
            if worker and self.can_afford(UnitTypeId.BARRACKS):
                worker.build(UnitTypeId.BARRACKS, barracks_placement_position)

        Moving a unit::

            # Move a random worker to the center of the map
            worker = self.workers.random_or(None)
            # worker can be None if all are dead
            if worker:
                worker.move(self.game_info.map_center)

        :param action:
        :param subtract_cost:
        :param subtract_supply:
        :param can_afford_check:
        """
        if not self.unit_command_uses_self_do and isinstance(action, bool):
            raise ValueError("You have used self.do(). This is no longer allowed in sharpy")

        assert isinstance(
            action, UnitCommand
        ), f"Given unit command is not a command, but instead of type {type(action)}"

        if subtract_cost:
            cost: Cost = self._game_data.calculate_ability_cost(action.ability)
            if can_afford_check and not (self.minerals >= cost.minerals and self.vespene >= cost.vespene):
                # Dont do action if can't afford
                return False
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene

        if subtract_supply and action.ability in abilityid_to_unittypeid:
            unit_type = abilityid_to_unittypeid[action.ability]
            required_supply = self.calculate_supply_cost(unit_type)
            # Overlord has -8
            if required_supply > 0:
                self.supply_used += required_supply
                self.supply_left -= required_supply

        if not self.knowledge.started or self.knowledge.action_handler.attempt_action(action):
            self.actions.append(action)
            self.unit_tags_received_action.add(action.unit.tag)
        return True
