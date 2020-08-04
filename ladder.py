# Run ladder game
# This lets python-sc2 connect to a LadderManager game: https://github.com/Cryptyc/Sc2LadderServer
# Based on: https://github.com/Dentosal/python-sc2/blob/master/examples/run_external.py
import argparse
import asyncio
import logging
import os
from datetime import datetime

import aiohttp

from config import get_config
from sc2 import Race, Difficulty
from sc2.client import Client

import sc2
from sc2.player import Computer, Human
from sc2.protocol import ConnectionAlreadyClosed
from sharpy.tools import LoggingUtility


def run_ladder_game(bot):
    # Load command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--GamePort", type=int, nargs="?", help="Game port")
    parser.add_argument("--StartPort", type=int, nargs="?", help="Start port")
    parser.add_argument("--LadderServer", type=str, nargs="?", help="Ladder server")
    parser.add_argument("--ComputerOpponent", type=str, nargs="?", help="Computer opponent")
    parser.add_argument("--ComputerRace", type=str, nargs="?", help="Computer race")
    parser.add_argument("--ComputerDifficulty", type=str, nargs="?", help="Computer difficulty")
    parser.add_argument("--OpponentId", type=str, nargs="?", help="Opponent ID")
    parser.add_argument("--RealTime", action="store_true", help="real time flag")
    args, unknown = parser.parse_known_args()

    if args.GamePort is None or args.StartPort is None:
        return stand_alone_game(bot), None

    if args.LadderServer is None:
        host = "127.0.0.1"
    else:
        host = args.LadderServer

    host_port = args.GamePort
    lan_port = args.StartPort

    # Add opponent_id to the bot class (accessed through self.opponent_id)
    bot.ai.opponent_id = args.OpponentId

    # Port config
    ports = [lan_port + p for p in range(1, 6)]

    portconfig = sc2.portconfig.Portconfig()
    portconfig.shared = ports[0]  # Not used
    portconfig.server = [ports[1], ports[2]]
    portconfig.players = [[ports[3], ports[4]]]

    opponent = args.OpponentId
    if not opponent:
        opponent = "unknown"

    folder = os.path.join("data", "games")
    if not os.path.isdir(folder):
        os.mkdir(folder)

    time = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
    file_name = f"{opponent}_{time}"
    path = f"{folder}/{file_name}.log"

    LoggingUtility.set_logger_file(log_level=get_config(False)["general"]["log_level"], path=path)

    # Join ladder game
    g = join_ladder_game(host=host, port=host_port, players=[bot], realtime=args.RealTime, portconfig=portconfig)

    # Run it
    result = asyncio.get_event_loop().run_until_complete(g)
    return result, args.OpponentId


# Modified version of sc2.main._join_game to allow custom host and port, and to not spawn an additional sc2process (thanks to alkurbatov for fix)
async def join_ladder_game(
    host, port, players, realtime, portconfig, save_replay_as=None, step_time_limit=None, game_time_limit=None
):
    ws_url = f"ws://{host}:{port}/sc2api"
    ws_connection = await aiohttp.ClientSession().ws_connect(ws_url, timeout=120)

    client = Client(ws_connection)

    try:
        result = await sc2.main._play_game(players[0], client, realtime, portconfig, step_time_limit, game_time_limit)
        if save_replay_as is not None:
            await client.save_replay(save_replay_as)
    except ConnectionAlreadyClosed:
        logging.error(f"Connection was closed before the game ended")
        return None
    finally:
        await ws_connection.close()

    return result


def stand_alone_game(bot):
    """
    Play a game against the ladder build or test the bot against ingame ai
    """
    print("Starting local game...")
    print("Play as human? (y / n)")
    input_human = input(">> ")
    map_name = "AcropolisLE"

    folder = os.path.join("data", "games")
    if not os.path.isdir(folder):
        os.mkdir(folder)
    time = datetime.now().strftime("%Y-%m-%d %H_%M_%S")

    if input_human and input_human.lower() == "y":
        races = ["p", "z", "t", "r"]
        race = None
        while race is None:
            print("Input your race (p / z / t / r):")
            human_race = input(">> ").lower()
            if human_race in races:
                if human_race == "p":
                    race = Race.Protoss
                elif human_race == "z":
                    race = Race.Zerg
                elif human_race == "t":
                    race = Race.Terran
                elif human_race == "r":
                    race = Race.Random
                else:
                    print(f'"{human_race}" not recognized.')

        file_name = f"Human{race}_{map_name}_{time}"
        path = f"{folder}/{file_name}.log"
        LoggingUtility.set_logger_file(log_level=get_config(False)["general"]["log_level"], path=path)

        return sc2.run_game(sc2.maps.get(map_name), [Human(race), bot], realtime=True)

    file_name = f"IngameAI_{map_name}_{time}"
    path = f"{folder}/{file_name}.log"
    LoggingUtility.set_logger_file(log_level=get_config(False)["general"]["log_level"], path=path)
    return sc2.run_game(sc2.maps.get(map_name), [bot, Computer(Race.Random, Difficulty.VeryHard)], realtime=False,)
