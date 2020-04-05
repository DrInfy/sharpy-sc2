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

        # async with SC2Process(fullscreen=False, port=port) as server:
        #     await server.ping()
        #
        #
        #     while True:
        #         pass
        #
        #     # client = Client(server._ws)
        #     # # Bot can decide if it wants to launch with 'raw_affects_selection=True'
        #     # if not isinstance(players[1], Human) and getattr(players[1].ai, "raw_affects_selection", None) is not None:
        #     #     client.raw_affects_selection = players[1].ai.raw_affects_selection
        #     #
        #     # try:
        #     #     result = await _play_game(players[1], client, realtime, portconfig, step_time_limit, game_time_limit)
        #     #     if save_replay_as is not None:
        #     #         await client.save_replay(save_replay_as)
        #     #     await client.leave()
        #     #     await client.quit()
        #     # except ConnectionAlreadyClosed:
        #     #     logging.error(f"Connection was closed before the game ended")
        #     #     return None
        #
        #     return None
    #

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

    # async def handle_proxy(self):
    #     """
    #     Handler for all requests. A client session is created for the bot and a connection to SC2 is made to forward
    #     all requests and responses.
    #     :param request:
    #     :return:
    #     """
    #
    #     self.process = self._launch("127.0.0.1", False)
    #     self.print("Starting client session")
    #
    #     start_time = time.monotonic()
    #     async with aiohttp.ClientSession() as session:
    #         await self.on_end(session)
    #         self.print("Websocket client connection starting")
    #
    #         # Set to 30 to detect internal bot crashes
    #         self.ws_c2p = WebSocketResponse(receive_timeout=30, max_msg_size=0)  # 0 == Unlimited
    #         # await self.ws_c2p.prepare(request)
    #         await self.on_end(self.ws_c2p)
    #
    #         url = "ws://localhost:" + str(self.ladder_player2_port) + "/sc2api"
    #         self.print("Websocket connection: " + str(url))
    #
    #         self.print("Connecting to SC2")
    #         self.ws_p2s = await self.await_startup(url)
    #         await self.on_end(self.ws_p2s)
    #         # async with await self.await_startup(url) as ws_p2s:  # Connects to SC2 instance
    #         c = Controller(self.ws_p2s, self.process)
    #         if not self.created_game:
    #             await self.create_game(c, players, self.map_name)
    #             self.created_game = True
    #
    #         self.print("Player:" + str(self.player_name))
    #         self.print("Joining game")
    #         self.print("Connecting proxy")
    #         try:
    #             async for msg in self.ws_c2p:
    #                 await self.check_time()  # Check for ties
    #                 if msg.data is None:
    #                     raise
    #
    #                 if not self.killed:  # Bot connection has not been closed, forward requests.
    #                     if msg.type == aiohttp.WSMsgType.BINARY:
    #                         req = await self.process_request(msg)
    #
    #                         if isinstance(req, bool):  # If process_request returns a bool, the request has been
    #                             # nullified. Return an empty response instead. TODO: Do this better
    #                             data_p2s = sc_pb.Response()
    #                             data_p2s.id = 0
    #                             data_p2s.status = 3
    #                             await self.ws_c2p.send_bytes(data_p2s.SerializeToString())
    #                         else:  # Nothing wrong with the request. Forward to SC2
    #                             await self.ws_p2s.send_bytes(req)
    #                             try:
    #                                 data_p2s = await self.ws_p2s.receive_bytes()  # Receive response from SC2
    #                                 await self.process_response(data_p2s)
    #                             except (
    #                                     asyncio.CancelledError,
    #                                     asyncio.TimeoutError,
    #                                     Exception
    #                             ) as e:
    #                                 self.print(str(e))
    #                             await self.ws_c2p.send_bytes(data_p2s)  # Forward response to bot
    #                         start_time = time.monotonic()  # Start the frame timer.
    #                     elif msg.type == aiohttp.WSMsgType.CLOSED:
    #                         self.print("Client shutdown")
    #                     else:
    #                         self.print("Incorrect message type")
    #                         await self.ws_c2p.close()
    #                 else:
    #                     self.print("Websocket connection closed")
    #                     raise ConnectionError
    #
    #         except Exception as e:
    #             IGNORED_ERRORS = {ConnectionError, asyncio.CancelledError}
    #             if not any([isinstance(e, E) for E in IGNORED_ERRORS]):
    #                 logger.error(str(e))
    #                 print(traceback.format_exc())
    #         finally:
    #             if not self._result:  # bot crashed, leave instead.
    #                 self.print("Bot crashed")
    #                 self._result = "Result.Crashed"
    #
    #
    #             self.print("Discarding proxy")
    #             request.app["websockets"].discard(self.ws_c2p)
    #
    #             self.print("Disconnected")
    #             self.print("Killing SC2")
    #             if self.process is not None and self.process.poll() is None:
    #                 for _ in range(3):
    #                     self.process.terminate()
    #                     time.sleep(0.5)
    #                     if self.process.poll() is not None:
    #                         break
    #                 else:
    #                     self.process.kill()
    #                     self.process.wait()
    #
    #             # return self.ws_p2s
    #
    #
    #     await self.on_end()

    def print(self, text: str):
        print(text)
