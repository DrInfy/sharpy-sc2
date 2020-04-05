import asyncio
import logging
import socket
from contextlib import contextmanager
import subprocess
import tempfile
import time
import warnings
from typing import Any
import numpy as np
import cv2
import aiohttp
import portpicker
from s2clientprotocol import sc2api_pb2 as sc_pb
import traceback

from sc2.controller import Controller

logger = logging.getLogger(__name__)
logger.setLevel(10)
logger.addHandler(logging.FileHandler("proxy.log", "a+"))

warnings.simplefilter("ignore", ResourceWarning)
warnings.simplefilter("ignore", ConnectionResetError)
warnings.simplefilter("ignore", RuntimeWarning)
warnings.simplefilter("ignore", AssertionError)
warnings.simplefilter("ignore", asyncio.CancelledError)


class ResponseBytesNotSet(Exception):
    pass


class Proxy:
    """
    Class for handling all requests/responses between bots and SC2. Receives and sends all relevant
    information(Game config, results etc) from and to the supervisor.
    """

    def __init__(
            self,
            port: int = None,
            game_created: bool = False,
            player_name: str = None,
            opponent_name: str = None,
    ):
        # self.supervisor: Supervisor = supervisor
        self.average_time: float = 0
        self.previous_loop: int = 0
        self.current_loop_frame_time: float = 0
        self._surrender: bool = False
        self.player_id: int = 0
        self.joined: bool = False
        self.killed: bool = False
        # self.replay_name: str = self.supervisor.replay_name
        self.port: int = port
        self.created_game: bool = game_created
        self._result: Any = None
        self.player_name: str = player_name
        self.opponent_name: str = opponent_name
        # self.map_name: str = self.supervisor.map
        # self.max_game_time: int = self.supervisor.max_game_time
        self._game_loops: int = 0
        self._game_time_seconds: float = 0
        self.ws_c2p = None
        self.ws_p2s = None
        self.no_of_strikes: int = 0
        # self.max_frame_time: int = self.supervisor.max_frame_time
        # self.strikes: int = self.supervisor.strikes
        self.replay_saved: bool = False
        # self.disable_debug: bool = self.supervisor.disable_debug
        # self.real_time: bool = self.supervisor.real_time
        # self.visualize: bool = self.supervisor.visualize
        self.render: bool = False
        self.observation_loaded = False
        self.game_info_loaded = False
        self.game_data_loaded = False
        self.visualize_step_count = 10
        self.process = None
        self.to_close = set()

    async def clean_up(self):
        try:
            if self.process is not None and self.process.poll() is None:
                for _ in range(3):
                    self.process.terminate()
                    time.sleep(0.5)
                    if self.process.poll() is not None:
                        break
                else:
                    self.process.kill()
                    self.process.wait()
                    logger.error("KILLED")
        except:
            print(traceback.format_exc())

        try:
            self.ws_c2p.close()
        except:
            print(traceback.format_exc())

        try:
            self.ws_p2s.close()
        except:
            print(traceback.format_exc())

    async def __request(self, request):
        """
        Sends a request to SC2 and returns a response
        :param request:
        :return:
        """
        try:
            await self.ws_p2s.send_bytes(request.SerializeToString())
        except TypeError:
            logger.debug("Cannot send: SC2 Connection already closed.")
            print(traceback.format_exc())

        response = sc_pb.Response()
        response_bytes = None
        try:
            response_bytes = await self.ws_p2s.receive_bytes()
        except TypeError:
            logger.exception("Cannot receive: SC2 Connection already closed.")
            print(traceback.format_exc())

        except asyncio.CancelledError:
            print(traceback.format_exc())
            try:
                await self.ws_p2s.receive_bytes()
            except asyncio.CancelledError:
                print(traceback.format_exc())
                logger.error("Requests must not be cancelled multiple times")

        except Exception as e:
            print(traceback.format_exc())
            logger.error(str(e))
        if response_bytes:
            response.ParseFromString(response_bytes)
        else:
            raise ResponseBytesNotSet("response_bytes not set")
        return response

    async def _execute(self, **kwargs):
        """
        Creates a request object from kwargs and return the response from __request.
        :param kwargs:
        :return:
        """
        assert len(kwargs) == 1, "Only one request allowed"

        request = sc_pb.Request(**kwargs)

        response = await self.__request(request)

        if response.error:
            logger.debug(f"{response.error}")

        return response

    async def check_time(self):
        """
        Used for detecting ties. Checks if _game_loops > max_game_time.
        :return:
        """
        if (
                self.max_game_time
                and self._game_loops > self.max_game_time
        ):
            self._result = "Result.Tie"
            self._game_time_seconds = (
                    self._game_loops / 22.4
            )

    async def check_for_result(self):
        """
        Called when game status has moved from in_game. Requests an observation from SC2 and populates self.player_id,
        self._result, self._game_loops from the observation.
        :return:
        """

        try:
            result = await self._execute(observation=sc_pb.RequestObservation())
            if not self.player_id:
                self.player_id = (
                    result.observation.observation.player_common.player_id
                )

            if result.observation.player_result:
                player_id_to_result = {
                    pr.player_id: Result(pr.result)
                    for pr in result.observation.player_result
                }
                self._result = player_id_to_result[self.player_id]
                self._game_loops = result.observation.observation.game_loop
                self._game_time_seconds = (
                        result.observation.observation.game_loop / 22.4
                )

        except Exception as e:
            print(traceback.format_exc())
            logger.error(e)

    async def create_game(self, server, players, map_name):
        """
        Static method to send a create_game request to SC2 with the relevant options.
        :param server:
        :param players:
        :param map_name:
        :return:
        """
        logger.debug("Creating game...")
        map_name = map_name.replace(".SC2Replay", "").replace(" ", "")
        response = await server.create_game(maps.get(map_name), players, realtime=self.real_time)
        logger.debug("Game created")
        return response

    def _launch(self, host: str, port: int = None, full_screen: bool = False):
        """
        Launches SC2 with the relevant arguments and returns a Popen process.This method also populates self.port if it
        isn't populated already.
        :param host: str
        :param port: int
        :param full_screen: bool
        :return:
        """
        if self.port is None:
            self.port = portpicker.pick_unused_port()
        else:
            self.port = port
        tmp_dir = tempfile.mkdtemp(prefix="SC2_")
        args = [
            str(Paths.EXECUTABLE),
            "-listen",
            host,
            "-port",
            str(self.port),
            "-displayMode",
            "1" if full_screen else "0",
            "-dataDir",
            str(Paths.BASE),
            "-tempDir",
            tmp_dir,
        ]

        return subprocess.Popen(args, cwd=(str(Paths.CWD) if Paths.CWD else None))

    async def save_replay(self):
        """
        Sends a save_replay request to SC2 and writes the response bytes to self.replay_name.
        :return: bool
        """
        if not self.replay_saved:
            logger.debug(f"Requesting replay from server")
            result = await self._execute(save_replay=sc_pb.RequestSaveReplay())
            if len(result.save_replay.data) > 10:
                with open(self.replay_name, "wb+") as f:
                    f.write(result.save_replay.data)
                logger.debug(f"Saved replay as " + str(self.replay_name))
            self.replay_saved = True
        return True

    async def process_request(self, msg):
        """
        Inspects and modifies requests. This method populates player_name in the join_game request, so that the bot name
        shows in game. Returns serialized message if the request is fine, otherwise returns a bool. This method also
        calls self.save_replay() and sets average_frame_time, game_time and game_time_seconds if a result is available.
        :param msg:
        :return:
        """
        request = sc_pb.Request()
        request.ParseFromString(msg.data)
        try:
            if not self.joined and str(request).startswith("join_game"):
                request.join_game.player_name = self.player_name
                request.join_game.options.raw_affects_selection = True
                if self.render:
                    request.join_game.options.render.resolution.x = 250
                    request.join_game.options.render.resolution.y = 250
                    request.join_game.options.render.minimap_resolution.x = 50
                    request.join_game.options.render.minimap_resolution.y = 50

                self.joined = True
                return request.SerializeToString()

            elif self.disable_debug and request.HasField("debug"):
                return False

            elif request.HasField('data'):
                request.data.unit_type_id = True
                request.data.upgrade_id = True
                request.data.buff_id = True
                request.data.effect_id = True
                request.data.ability_id = True
                return request.SerializeToString()

            elif request.HasField("leave_game"):
                logger.debug(f'{self.player_name} has issued a LeaveGameRequest')

                self._surrender = True
                self._result = "Result.Defeat"
                return msg.data

        except Exception as e:
            logger.debug(f"Exception{e}")
            print(traceback.format_exc())

        if self._result:
            try:
                if {
                    self.player_name: self.average_time / self._game_loops
                } not in self.supervisor.average_frame_time:
                    self.supervisor.average_frame_time = {
                        self.player_name: self.average_time / self._game_loops
                    }
            except ZeroDivisionError:
                print(traceback.format_exc())
                self.supervisor.average_frame_time = {self.player_name: 0}
            self.supervisor.game_time = self._game_loops
            self.supervisor.game_time_seconds = self._game_time_seconds

            if await self.save_replay():
                if self._surrender:
                    await self._execute(leave_game=sc_pb.RequestLeaveGame())
                self.killed = True
                return request.SerializeToString()
        return msg.data

    async def process_response(self, msg):
        """
        Uses responses from SC2 to populate self._game_loops instead of sending extra requests to SC2. Also calls
        self.check_for_result() if the response status is > 3(in_game).
        :param msg:
        :return:
        """
        response = sc_pb.Response()
        response.ParseFromString(msg)
        visualize_step = self._game_loops % self.visualize_step_count == 0 or self._game_loops < 10
        if response.HasField('observation'):
            self._game_loops = response.observation.observation.game_loop
            if self.render:
                raise NotImplemented

            if self.visualize and visualize_step:
                self.observation_loaded = True
                await self.mini_map.load_state(response)

        elif self.visualize and not self.game_info_loaded and response.HasField('game_info'):
            self.game_info_loaded = True
            self.mini_map.load_game_info(response)

        elif self.visualize and not self.game_data_loaded and response.HasField('data'):
            self.game_data_loaded = True
            self.mini_map.load_game_data(response)

        if self.visualize and self.game_info_loaded and self.observation_loaded and self.game_data_loaded \
                and visualize_step:
            self.mini_map.player_name = self.player_name
            image = await self.mini_map.draw_map()
            score = await self.mini_map.get_score()
            self.supervisor.images[self.player_name]['image'] = image
            self.supervisor.images[self.player_name]['score'] = score

        if response.status > 3:
            await self.check_for_result()

    async def on_end(self, object=None):
        if object is not None:
            self.to_close.add(object)
        else:
            for o in self.to_close:
                await o.close()

    async def await_startup(self, url):
        for i in range(60):
            try:
                session = aiohttp.ClientSession()
                ws = await session.ws_connect(url, timeout=120)
                logger.debug("Websocket connection ready")
                await self.on_end(session)
                return ws
            except aiohttp.client_exceptions.ClientConnectorError:
                await asyncio.sleep(1)
                await session.close()
                if i > 15:
                    logger.debug("Connection refused (startup not complete (yet))")

    async def websocket_handler(self, request):
        """
        Handler for all requests. A client session is created for the bot and a connection to SC2 is made to forward
        all requests and responses.
        :param request:
        :return:
        """
        logger.debug("Launching SC2")
        self.process = self._launch("127.0.0.1", False)
        logger.debug("Starting client session")
        start_time = time.monotonic()
        async with aiohttp.ClientSession() as session:
            await self.on_end(session)
            logger.debug("Websocket client connection starting")

            # Set to 30 to detect internal bot crashes
            self.ws_c2p = aiohttp.web.WebSocketResponse(receive_timeout=30, max_msg_size=0)  # 0 == Unlimited
            await self.ws_c2p.prepare(request)
            await self.on_end(self.ws_c2p)
            request.app["websockets"].add(self.ws_c2p)  # Add bot client to WeakSet for use in detecting amount of
            # clients connected

            players = [
                Bot(None, None, name=self.player_name),
                Bot(None, None, name=self.opponent_name),
            ]

            self.supervisor.pids = self.process.pid  # Add SC2 to supervisor pid list for use in cleanup

            url = "ws://localhost:" + str(self.port) + "/sc2api"
            logger.debug("Websocket connection: " + str(url))

            logger.debug("Connecting to SC2")
            self.ws_p2s = await self.await_startup(url)
            await self.on_end(self.ws_p2s)
            # async with await self.await_startup(url) as ws_p2s:  # Connects to SC2 instance
            c = Controller(self.ws_p2s, self.process)
            if not self.created_game:
                await self.create_game(c, players, self.map_name)
                self.created_game = True

            logger.debug("Player:" + str(self.player_name))
            logger.debug("Joining game")
            logger.debug("Connecting proxy")
            try:
                async for msg in self.ws_c2p:
                    await self.check_time()  # Check for ties
                    if msg.data is None:
                        raise

                    # Detect slow bots. TODO: Move to own method
                    if self.previous_loop < self._game_loops:  # New loop. Add frame time to average time and reset
                        # current frame time.
                        self.average_time += self.current_loop_frame_time
                        self.previous_loop = self._game_loops

                        if self.current_loop_frame_time * 1000 > self.max_frame_time:  # If bot's current frame is
                            # slower than max allowed, increment strike counter.
                            self.no_of_strikes += 1

                        elif self.no_of_strikes > 0:  # We don't want bots to build up a "credit"
                            self.no_of_strikes -= 1

                        self.current_loop_frame_time = 0

                    else:
                        self.current_loop_frame_time += (time.monotonic() - start_time)

                    if self.no_of_strikes > self.strikes:  # Bot exceeded max_frame_time, surrender on behalf of bot
                        logger.debug(f'{self.player_name} exceeded {self.max_frame_time} ms, {self.no_of_strikes} '
                                     f'times in a row')

                        self._surrender = True
                        self._result = "Result.Timeout"

                    if not self.killed:  # Bot connection has not been closed, forward requests.
                        if msg.type == aiohttp.WSMsgType.BINARY:
                            req = await self.process_request(msg)

                            if isinstance(req, bool):  # If process_request returns a bool, the request has been
                                # nullified. Return an empty response instead. TODO: Do this better
                                data_p2s = sc_pb.Response()
                                data_p2s.id = 0
                                data_p2s.status = 3
                                await self.ws_c2p.send_bytes(data_p2s.SerializeToString())
                            else:  # Nothing wrong with the request. Forward to SC2
                                await self.ws_p2s.send_bytes(req)
                                try:
                                    data_p2s = await self.ws_p2s.receive_bytes()  # Receive response from SC2
                                    await self.process_response(data_p2s)
                                except (
                                        asyncio.CancelledError,
                                        asyncio.TimeoutError,
                                        Exception
                                ) as e:
                                    logger.error(str(e))
                                    print(traceback.format_exc())
                                await self.ws_c2p.send_bytes(data_p2s)  # Forward response to bot
                            start_time = time.monotonic()  # Start the frame timer.
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.error("Client shutdown")
                        else:
                            logger.error("Incorrect message type")
                            await self.ws_c2p.close()
                    else:
                        logger.debug("Websocket connection closed")
                        raise ConnectionError

            except Exception as e:
                IGNORED_ERRORS = {ConnectionError, asyncio.CancelledError}
                if not any([isinstance(e, E) for E in IGNORED_ERRORS]):
                    logger.error(str(e))
                    print(traceback.format_exc())
            finally:
                if not self._result:  # bot crashed, leave instead.
                    logger.debug("Bot crashed")
                    self._result = "Result.Crashed"
                try:
                    if await self.save_replay():
                        await self._execute(leave_game=sc_pb.RequestLeaveGame())
                except Exception:
                    print(traceback.format_exc())
                    logger.debug("Can't save replay, SC2 already closed")
                try:
                    if {
                        self.player_name: self.average_time / self._game_loops
                    } not in self.supervisor.average_frame_time:
                        self.supervisor.average_frame_time = {
                            self.player_name: self.average_time / self._game_loops
                        }
                except ZeroDivisionError:
                    self.supervisor.average_frame_time = {self.player_name: 0}
                if self.visualize and False:  # TODO: fix for new visualization
                    img = np.ones((500, 500, 3))
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    org = (50, 50)
                    font_scale = 1
                    color = (50, 194, 134)
                    thickness = 1

                    flipped = cv2.resize(img, (500, 500), cv2.INTER_NEAREST)
                    cv2.putText(flipped, self.player_name, org, font, font_scale, color, thickness, cv2.LINE_AA)
                    if self._result:
                        cv2.putText(flipped, str(self._result), (50, 200), font, font_scale, color, thickness,
                                    cv2.LINE_AA)

                self.supervisor.result = dict({self.player_name: self._result})

                logger.debug("Discarding proxy")
                request.app["websockets"].discard(self.ws_c2p)

                logger.debug("Disconnected")
                logger.debug("Killing SC2")
                if self.process is not None and self.process.poll() is None:
                    for _ in range(3):
                        self.process.terminate()
                        time.sleep(0.5)
                        if self.process.poll() is not None:
                            break
                    else:
                        self.process.kill()
                        self.process.wait()

                # return self.ws_p2s
        await self.on_end()
