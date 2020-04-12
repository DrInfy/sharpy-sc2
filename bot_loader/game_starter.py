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
from sc2.player import AbstractPlayer, Bot
from sharpy.knowledges import KnowledgeBot

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
    "SimulacrumLE",
    "ZenLE",
    "NightshadeLE",
)


class GameStarter:
    def __init__(self, definitions: BotDefinitions) -> None:
        self.config = get_config()

        log_level = self.config["general"]["log_level"]

        self.root_logger = logging.getLogger()

        # python-sc2 logs a ton of spam with log level DEBUG. We do not want that.
        self.root_logger.setLevel(log_level)

        # Remove handlers from python-sc2 so we don't get the same messages twice.
        for handler in sc2.main.logger.handlers:
            sc2.main.logger.removeHandler(handler)

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
            "-map",
            help="Name of the map. The script works with any map present in Starcraft 2 Maps directory.",
            default="random",
        )
        parser.add_argument("-p1", "--player1", help="Name of player 1 human / bot.")
        parser.add_argument("-p2", "--player2", help="Name of the enemy bot.", default="random")
        parser.add_argument("-rt", "--real-time", help="Use real-time mode.", action="store_true")
        parser.add_argument("-human", "--human", help="Human vs bot mode. Specify race with lower case")
        parser.add_argument(
            "-release", "--release", help="Uses only release config and ignore config local", action="store_true"
        )
        parser.add_argument("-raw", "--raw_selection", help="Raw affects selection.", action="store_true")

        args = parser.parse_args()

        bot_text = "random"

        if args.human:
            bot_text = "human." + args.human
            args.real_time = True
            args.release = True

        if args.player1:
            bot_text = args.player1
        elif bot_text == "random":
            bot_text = random.choice(list(self.random_bots.keys()))

        map_name = args.map
        if map_name == "random":
            map_name = random.choice(self.random_maps)

        if map_name not in self.maps:
            print(f"map not in Maps:{new_line}{new_line.join(self.maps)}")
            return

        enemy_text = args.player2
        if enemy_text == "random":
            enemy_text = random.choice(list(self.random_bots.keys()))

        enemy_split: List[str] = enemy_text.split(".")
        enemy_type = enemy_split.pop(0)

        bot_split: List[str] = bot_text.split(".")
        bot_type = bot_split.pop(0)

        if bot_type not in self.definitions.player1:
            keys = list(self.definitions.player1.keys())
            print(f"Player1 type {bot_text} not found in:{new_line} {new_line.join(keys)}")
            return

        enemy: Optional[AbstractPlayer]

        if enemy_type not in self.definitions.player2:
            # loader = BotLoader()
            # root_dir = os.path.dirname(os.path.abspath(__file__))
            # path = os.path.join("Bots")
            # path = os.path.join(root_dir, path)
            # loader.get_bots(path)
            # enemy = loader.get_bot(enemy_type)
            # if not enemy:
            keys = list(self.definitions.player2.keys())
            print(f"Enemy type {enemy_type} not found in player types:{new_line}{new_line.join(keys)}")
            return
        else:
            enemy = self.players[enemy_type](enemy_split)

        bot: AbstractPlayer = self.players[bot_type](bot_split)

        folder = "games"
        if not os.path.isdir(folder):
            os.mkdir(folder)

        time = datetime.now().strftime("%Y-%m-%d %H_%M_%S")
        randomizer = random.randint(0, 999999)
        # Randomizer is to make it less likely that games started at the same time have same neme
        file_name = f"{enemy_text}_{map_name}_{time}_{randomizer}"
        path = f"{folder}/{file_name}.log"

        handler = logging.FileHandler(path)
        self.root_logger.addHandler(handler)

        GameStarter.setup_bot(bot, bot_text, enemy_text, args)
        GameStarter.setup_bot(enemy, enemy_text, bot_text, args)

        print(f"Starting game in {map_name}.")
        print(f"{bot_text} vs {enemy_text}")

        runner = MatchRunner()
        runner.run_game(
            maps.get(map_name),
            [bot, enemy],
            player1_id=bot_text,
            realtime=args.real_time,
            game_time_limit=(30 * 60),
            save_replay_as=f"{folder}/{file_name}.SC2Replay",
        )

        # release file handle
        self.root_logger.removeHandler(handler)
        handler.close()

    @staticmethod
    def setup_bot(player: AbstractPlayer, bot_code, enemy_text: str, args):
        if isinstance(player, Bot) and hasattr(player.ai, "config"):
            my_bot: KnowledgeBot = player.ai
            my_bot.opponent_id = bot_code + "-" + enemy_text
            my_bot.run_custom = True
            my_bot.raw_affects_selection = args.raw_selection
            if args.release:
                my_bot.config = get_config(False)
