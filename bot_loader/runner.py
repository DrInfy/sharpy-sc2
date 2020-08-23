import subprocess
import tempfile
import time
from typing import List, Any, Optional

import portpicker
from aiohttp.web_ws import WebSocketResponse

from bot_loader.killable_process import KillableProcess
from bot_loader.ladder_bot import BotLadder
from bot_loader.port_picker import pick_contiguous_unused_ports, return_ports
from sc2 import run_game

# noinspection PyProtectedMember
from sc2.main import _host_game
from sc2.paths import Paths
from sc2.player import AbstractPlayer
import asyncio

from sc2.portconfig import Portconfig


class MatchRunner:
    def __init__(self) -> None:
        self.ladder_player2_port = None
        self.process = None
        self.to_close = set()

        self.ws_c2p: Optional[WebSocketResponse] = None

        super().__init__()

    def run_game(
        self, map_settings: str, players: List[AbstractPlayer], player1_id: str, start_port: Optional[str], **kwargs
    ):
        if isinstance(players[0], BotLadder):
            raise Exception("Player 1 cannot be a ladder bot!")

        # Port config
        if start_port:
            ports = range(int(start_port), int(start_port) + 7)
        else:
            ports = pick_contiguous_unused_ports(7)
        portconfig = Portconfig()

        portconfig.shared = ports[0]  # Not used
        portconfig.server = [ports[1], ports[2]]
        portconfig.players = [[ports[3], ports[4]], [ports[5], ports[6]]]

        if len(players) > 1 and isinstance(players[1], BotLadder):
            # host_only_args = ["save_replay_as", "rgb_render_config", "random_seed", "sc2_version"]

            self.ladder_player2_port = portconfig.players[1][0]

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

            return_ports(ports)

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
        port = self.ladder_player2_port
        self.print(f"Staring client server with port {port}")
        KillableProcess(await self._launch("127.0.0.1", port, False))
        time.sleep(5)
        KillableProcess(await ladder_bot.join_game(opponent_id, portconfig=portconfig))

        # We'll have to host handle the rest

    async def _launch(self, host: str, port: int, full_screen: bool = False) -> Any:
        """
        Launches SC2 with the relevant arguments and returns a Popen process.This method also populates self.port if it
        isn't populated already.
        :param host: str
        :param port: int
        :param full_screen: bool
        :return:
        """

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
            "--verbose",
        ]

        return subprocess.Popen(args, cwd=(str(Paths.CWD) if Paths.CWD else None))

    def print(self, text: str):
        print(text)
