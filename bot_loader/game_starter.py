import glob
import logging
import os
import random
import sys
import argparse
from datetime import datetime
from typing import List, Optional, Dict

from bot_loader import BotLadder
from bot_loader.bot_definitions import BotDefinitions, races, builds, difficulty
from config import get_config
import sc2
from bot_loader.loader import BotLoader
from bot_loader.runner import MatchRunner
from sc2 import maps
from sc2.paths import Paths
from sc2.player import AbstractPlayer, Bot, Human
from sharpy.knowledges import KnowledgeBot
from sharpy.tools import LoggingUtility

new_line = "\n"

# Used for random map selection
known_melee_maps = (
    "AbyssalReefLE",
    "AcolyteLE",
    "(2)RedshiftLE",
    "(2)DreamcatcherLE",
    "(2)LostandFoundLE",
    "AutomatonLE",
    "BlueshiftLE",
    "CeruleanFallLE",
    "DarknessSanctuaryLE",
    "KairosJunctionLE",
    "ParaSiteLE",
    "PortAleksanderLE",
    # "StasisLE", # Bugged map for bots
    "CyberForestLE",
    "KingsCoveLE",
    "NewRepugnancyLE",
    # Season 3 2019
    "AcropolisLE",
    "DiscoBloodbathLE",
    "EphemeronLE",
    "ThunderbirdLE",
    "TritonLE",
    "WintersGateLE",
    "WorldofSleepersLE",
    # Season 1 2020
    "SImulacrumLE",
    "ZenLE",
    "NightshadeLE",
)


class GameStarter:
    def __init__(self, definitions: BotDefinitions) -> None:
        self.config = get_config()

        self.definitions = definitions
        self.players = definitions.playable
        self.random_bots = definitions.random_bots

        self.maps = GameStarter.installed_maps()
        self.random_maps = [x for x in known_melee_maps if x in self.maps]

    @staticmethod
    def installed_maps() -> List[str]:
        maps_folder = Paths.MAPS
        map_file_paths = glob.glob(f"{maps_folder}/**/*.SC2Map", recursive=True)

        def get_file_name(path) -> str:
            filename_w_ext = os.path.basename(path)
            filename, file_ext = os.path.splitext(filename_w_ext)
            return filename

        # Use a set to remove duplicate names (same map in multiple folders)
        map_file_names = set(map(get_file_name, map_file_paths))

        map_list = []
        for file_name in sorted(map_file_names):
            map_list.append(file_name)
        return map_list

    def play(self):
        # noinspection PyTypeChecker
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="Run a game with custom parameters.",
            epilog=f"""\
Installed maps:
{new_line.join(sorted(self.maps))}

Bots:
{new_line.join(sorted(self.players.keys()))}


For ingame ai, use ai.race.difficulty.build where all arguments are optional
ingame ai defaults to ai.random.veryhard.random

Races:
{new_line.join(races.keys())}

Difficulties:
{new_line.join(difficulty.keys())}

Builds:
{new_line.join(builds.keys())}
                """,
        )

        parser.add_argument(
            "-m",
            "--map",
            help="Name of the map. Defaults to random. The script works with any map present in Starcraft 2 Maps directory.",
            default="random",
        )
        parser.add_argument(
            "-p1", "--player1", help="Name of player 1 bot or human. Defaults to random.", default="random"
        )
        parser.add_argument("-p2", "--player2", help="Name of player 2 bot. Defaults to random.", default="random")
        parser.add_argument("-rt", "--real-time", help="Use real-time mode.", action="store_true")
        parser.add_argument(
            "-r", "--release", help="Use only release config and ignore config local.", action="store_true"
        )
        parser.add_argument("-raw", "--raw_selection", help="Raw affects selection.", action="store_true")
        parser.add_argument(
            "--port", help="starting port to use, i.e. 10 would result in ports 10-17 being used to play."
        )

        args = parser.parse_args()

        player1: str = args.player1

        if player1 == "random":
            player1 = random.choice(list(self.random_bots.keys()))
        elif "human" in player1:
            args.real_time = True
            args.release = True

        map_name = args.map
        if map_name == "random":
            map_name = random.choice(self.random_maps)

        if map_name not in self.maps:
            print(f"map not in Maps:{new_line}{new_line.join(self.maps)}")
            return

        player2: str = args.player2
        if player2 == "random":
            player2 = random.choice(list(self.random_bots.keys()))

        player2_split: List[str] = player2.split(".")
        player2_type: str = player2_split.pop(0)

        player1_split: List[str] = player1.split(".")
        player1_type: str = player1_split.pop(0)

        if player1_type not in self.definitions.player1:
            keys = list(self.definitions.player1.keys())
            print(f"Player1 type {player1} not found in:{new_line} {new_line.join(keys)}")
            return

        player2_bot: Optional[AbstractPlayer]

        if player2_type not in self.definitions.player2:
            keys = list(self.definitions.player2.keys())
            print(f"Enemy type {player2_type} not found in player types:{new_line}{new_line.join(keys)}")
            return
        else:
            player2_bot = self.players[player2_type](player2_split)

        player1_bot: AbstractPlayer = self.players[player1_type](player1_split)

        folder = "games"
        if not os.path.isdir(folder):
            os.mkdir(folder)

        time = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
        randomizer = random.randint(0, 999999)
        # Randomizer is to make it less likely that games started at the same time have same name
        file_name = f"{player2}_{map_name}_{time}_{randomizer}"
        path = f"{folder}/{file_name}.log"
        LoggingUtility.set_logger_file(log_level=self.config["general"]["log_level"], path=path)

        GameStarter.setup_bot(player1_bot, player1, player2, args)
        GameStarter.setup_bot(player2_bot, player2, player1, args)

        print(f"Starting game in {map_name}.")
        print(f"{player1} vs {player2}")

        runner = MatchRunner()
        runner.run_game(
            maps.get(map_name),
            [player1_bot, player2_bot],
            player1_id=player1,
            realtime=args.real_time,
            game_time_limit=(30 * 60),
            save_replay_as=f"{folder}/{file_name}.SC2Replay",
            start_port=args.port,
        )

        # release file handle
        sc2.main.logger.remove()

    @staticmethod
    def setup_bot(player: AbstractPlayer, bot_code, enemy_text: str, args):
        if isinstance(player, Human):
            player.fullscreen = True
        if isinstance(player, Bot) and hasattr(player.ai, "config"):
            my_bot: KnowledgeBot = player.ai
            my_bot.opponent_id = bot_code + "-" + enemy_text
            my_bot.run_custom = True
            my_bot.raw_affects_selection = args.raw_selection
            if args.release:
                my_bot.config = get_config(False)
