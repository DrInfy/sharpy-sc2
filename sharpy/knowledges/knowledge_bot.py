import logging
import sys
import threading
from abc import abstractmethod

from sc2.units import Units
from sharpy.knowledges import Knowledge
from sharpy.plans import BuildOrder
from config import get_config, get_version
from sc2 import BotAI, Result, Optional, UnitTypeId
from sc2.unit import Unit
import time


class KnowledgeBot(BotAI):
    """Base class for bots that are built around Knowledge class."""
    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self.config = get_config()
        self.knowledge: Knowledge = None
        self.plan: BuildOrder = None
        self.knowledge = Knowledge()
        self.start_plan = True
        self.run_custom = False
        self.realtime_worker = True
        self.realtime_split = True
        self.last_game_loop = -1
        self.distance_calculation_method = 0

    async def real_init(self):
        self.knowledge.pre_start(self)
        await self.knowledge.start()
        self.plan = await self.create_plan()
        if self.start_plan:
            await self.plan.start(self.knowledge)

        self._log_start()

    async def chat_init(self):
        if self.knowledge.is_chat_allowed:
            msg = self._create_start_msg()
            await self.chat_send(msg)

    def _create_start_msg(self) -> str:
        msg: str = ""

        if self.name is not None:
            msg += self.name

        version = get_version()
        if len(version) >= 2:
            msg += f" {version[0]} {version[1]}"

        return msg

    async def chat_send(self, message: str):
        # todo: refactor to use chat manager?
        self.knowledge.print(message, "Chat")
        await super().chat_send(message)

    @abstractmethod
    async def create_plan(self) -> BuildOrder:
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
        self._client.game_step = int(self.config["general"]["game_step_size"])

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

    async def on_start(self):
        """Allows initializing the bot when the game data is available."""
        await self.real_init()

    async def on_step(self, iteration):
        try:
            if iteration == 10:
                await self.chat_init()

            if not self.realtime and self.last_game_loop == self.state.game_loop:
                self.realtime = True
                self.client.game_step = 1
                return

            self.last_game_loop = self.state.game_loop

            ns_step = time.perf_counter_ns()
            await self.knowledge.update(iteration)
            await self.pre_step_execute()
            await self.plan.execute()

            await self.knowledge.post_update()

            if self.knowledge.debug:
                await self.plan.debug_draw()

            ns_step = time.perf_counter_ns() - ns_step
            ms_step = ns_step / 1000 / 1000

            if ms_step > 100:
                self.knowledge.print(f"Step {self.state.game_loop} took {round(ms_step)} ms.",
                                     "LAG", stats=False, log_level=logging.WARNING)


        except:  # catch all exceptions
            e = sys.exc_info()[0]
            logging.exception(e)

            # do we want to raise the exception and crash? or try to go on? :/
            raise

    async def pre_step_execute(self):
        pass

    async def on_unit_destroyed(self, unit_tag: int):
        if self.knowledge.ai is not None:
            await self.knowledge.on_unit_destroyed(unit_tag)

    async def on_unit_created(self, unit: Unit):
        if self.knowledge.ai is not None:
            await self.knowledge.on_unit_created(unit)

    async def on_building_construction_started(self, unit: Unit):
        if self.knowledge.ai is not None:
            await self.knowledge.on_building_construction_started(unit)

    async def on_building_construction_complete(self, unit: Unit):
        if self.knowledge.ai is not None:
            await self.knowledge.on_building_construction_complete(unit)

    async def on_end(self, game_result: Result):
        if self.knowledge.ai is not None:
            await self.knowledge.on_end(game_result)

    def _log_start(self):
        def log(message):
            self.knowledge.print(message, tag="Start", stats=False)

        log(f"My race: {self.knowledge.my_race.name}")
        log(f"Opponent race: {self.knowledge.enemy_race.name}")
        log(f"OpponentId: {self.opponent_id}")

    async def start_first_worker(self):
        if self.townhalls and self.realtime_worker:
            townhall = self.townhalls.first
            if townhall.type_id == UnitTypeId.COMMANDCENTER:
                await self.synchronous_do(townhall.train(UnitTypeId.SCV))
            if townhall.type_id == UnitTypeId.NEXUS:
                await self.synchronous_do(townhall.train(UnitTypeId.PROBE))
            if townhall.type_id == UnitTypeId.HATCHERY:
                await self.synchronous_do(townhall.train(UnitTypeId.DRONE))
