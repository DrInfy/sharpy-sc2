import logging
import string
from configparser import ConfigParser
from typing import Any, Optional

from sc2.main import logger
from sharpy.interfaces import ILogManager
from .manager_base import ManagerBase

root_logger = logging.getLogger()


class LogManager(ManagerBase, ILogManager):
    config: ConfigParser
    logger: Any  # TODO: type?
    start_with: Optional[str]

    def __init__(self) -> None:
        super().__init__()
        self.start_with = None

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.logger = logger
        self.config = knowledge.config

    async def update(self):
        pass

    async def post_update(self):
        pass

    def print(self, message: string, tag: string = None, stats: bool = True, log_level=logging.INFO):
        """
        Prints a message to log.

        :param message: The message to print.
        :param tag: An optional tag, which can be used to indicate the logging component.
        :param stats: When true, stats such as time, minerals, gas, and supply are added to the log message.
        :param log_level: Optional logging level. Default is INFO.
        """

        if self.ai.run_custom and self.ai.player_id != 1 and not self.ai.realtime:
            # No logging for player 2 in custom games
            return

        if tag is not None:
            debug_log = self.config["debug_log"]
            enabled = debug_log.getboolean(tag, fallback=True)
            if not enabled:
                return

        if tag is not None:
            message = f"[{tag}] {message}"

        if stats:
            last_step_time = round(self.ai.step_time[3])

            message = (
                f"{self.ai.time_formatted.rjust(5)} {str(last_step_time).rjust(4)}ms "
                f"{str(self.ai.minerals).rjust(4)}M {str(self.ai.vespene).rjust(4)}G "
                f"{str(self.ai.supply_used).rjust(3)}/{str(self.ai.supply_cap).rjust(3)}U {message}"
            )

        if self.start_with:
            message = self.start_with + message
        self.logger.log(log_level, message)
