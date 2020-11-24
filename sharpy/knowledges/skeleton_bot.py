import logging
import sys
import time

from sc2 import BotAI, UnitTypeId
from sc2.units import Units
from config import get_config, get_version
from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, List
from sharpy.knowledges.skeleton_knowledge import SkeletonKnowledge


if TYPE_CHECKING:
    from sharpy.managers import ManagerBase
    from sc2.unit import Unit


class SkeletonBot(BotAI):
    def __init__(self, name: str):
        self.knowledge = SkeletonKnowledge()
        self.name = name
        self.config = get_config()
        # This is needed to know whether this is a custom run or game created by ladder manager
        self.run_custom = False
        self.realtime_worker = True
        self.realtime_split = True

        self.last_game_loop = -1

        self.distance_calculation_method = 0
        # TODO: Remove this
        self.unit_command_uses_self_do = True
        # In general it is better to fail fast and early in order to fix things.
        self.crash_on_except = True

    async def on_start(self):
        """Allows initializing the bot when the game data is available."""
        self.knowledge.pre_start(self, self.configure_managers())
        await self.knowledge.start()

        # self._log_start()

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
        self._client.game_step = int(self.config["general"]["game_step_size"])

    async def split_workers(self):
        if self.realtime_split:
            # Split workers
            mfs = self.mineral_field.closer_than(10, self.townhalls.first.position)
            workers = Units(self.workers, self)

            for mf in mfs:  # type: Unit
                if workers:
                    worker = workers.closest_to(mf)
                    self.do(worker.gather(mf))
                    workers.remove(worker)

            for w in workers:  # type: Unit
                self.do(w.gather(mfs.closest_to(w)))
            await self._do_actions(self.actions)
            self.actions.clear()

    async def start_first_worker(self):
        if self.townhalls and self.realtime_worker:
            townhall = self.townhalls.first
            if townhall.type_id == UnitTypeId.COMMANDCENTER:
                await self.synchronous_do(townhall.train(UnitTypeId.SCV))
            if townhall.type_id == UnitTypeId.NEXUS:
                await self.synchronous_do(townhall.train(UnitTypeId.PROBE))
            if townhall.type_id == UnitTypeId.HATCHERY:
                await self.synchronous_do(townhall.train(UnitTypeId.DRONE))
