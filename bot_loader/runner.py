import subprocess
import tempfile
import time
from subprocess import Popen
from typing import List, Any, Optional

import aiohttp
import portpicker
from aiohttp.web_ws import WebSocketResponse

from bot_loader.ladder_bot import BotLadder
from bot_loader.sc2only_process import SC2OnlyProcess
from sc2 import run_game, sc_pb
from sc2.controller import Controller
from sc2.main import _host_game
from sc2.paths import Paths
from sc2.player import Human, Bot, AbstractPlayer
import asyncio

from sc2.portconfig import Portconfig
from sc2.sc2process import SC2Process


class MatchRunner():
    def __init__(self) -> None:
        self.ladder_player2_port = None
        self.process = None
        self.to_close = set()

        self.ws_c2p: Optional[WebSocketResponse] = None

        super().__init__()

    def run_game(self, map_settings: str,  players: List[AbstractPlayer], player1_id: str, **kwargs):
        if isinstance(players[0], BotLadder):
            raise Exception('Player 1 cannot be a ladder bot!')
        if len(players) > 1 and isinstance(players[1], BotLadder):
            # host_only_args = ["save_replay_as", "rgb_render_config", "random_seed", "sc2_version"]

            portconfig = Portconfig()
            self.ladder_player2_port = portconfig.server[1]

            # noinspection PyTypeChecker
            ladder_bot: BotLadder = players[1]
            opponent_id = player1_id  # players[0].name
            result = asyncio.get_event_loop().run_until_complete(
                asyncio.gather(
                    _host_game(map_settings, players, **kwargs, portconfig=portconfig),
                    self.join_game(ladder_bot, False, portconfig, opponent_id)
                    # ladder_bot.join_game(opponent_id, portconfig=portconfig)
                )
            )

            return result
        else:
            return run_game(map_settings, players, **kwargs)

    async def join_game(
            self,
            ladder_bot: BotLadder,
            realtime,
            portconfig: Portconfig,
            opponent_id,
            save_replay_as=None,
            step_time_limit=None,
            game_time_limit=None,
    ):
        port = portconfig.server[1]
        self.print(f"Staring client server with port {port}")
        process_id = await self._launch("127.0.0.1", port, False)
        time.sleep(5)
        pid = await ladder_bot.join_game(opponent_id, portconfig=portconfig)
        # while True:
        #     time.sleep(1)


    async def _launch(self, host: str, port: int = None, full_screen: bool = False) -> Any:
        """
        Launches SC2 with the relevant arguments and returns a Popen process.This method also populates self.port if it
        isn't populated already.
        :param host: str
        :param port: int
        :param full_screen: bool
        :return:
        """

        if port is None:
            port = portpicker.pick_unused_port()
        else:
            port = port
        tmp_dir = tempfile.mkdtemp(prefix="SC2_")
        args = [
            str(Paths.EXECUTABLE),
            "-listen",
            host,
            "-port",
            str(port),
            "-displayMode",
            "1" if full_screen else "0",
            "-dataDir",
            str(Paths.BASE),
            "-tempDir",
            tmp_dir,
            "--verbose"
        ]

        return subprocess.Popen(args, cwd=(str(Paths.CWD) if Paths.CWD else None))

    def print(self, text: str):
        print(text)
