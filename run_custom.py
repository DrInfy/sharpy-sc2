import argparse
import datetime
import glob
import logging
import os
import random
from typing import List
import sys

sys.path.insert(1, "python-sc2")

from sharpy.knowledges import KnowledgeBot


import sc2
from config import get_config
from dummies.protoss import *
from dummies.terran import *
from dummies.zerg import *
from dummies.debug import *
from examples.terran.mass_reaper import MassReaperBot
from examples.terran.proxy_rax import ProxyRaxBot
from examples.worker_rush import WorkerRushBot
from sc2 import run_game, maps, Race, Difficulty, AIBuild
from sc2.paths import Paths
from sc2.player import Bot, Computer, AbstractPlayer, Human

from version import update_version_txt

update_version_txt()

config = get_config()

log_level = config["general"]["log_level"]

root_logger = logging.getLogger()

# python-sc2 logs a ton of spam with log level DEBUG. We do not want that.
root_logger.setLevel(log_level)

# Remove handlers from python-sc2 so we don't get the same messages twice.
for handler in sc2.main.logger.handlers:
    sc2.main.logger.removeHandler(handler)

new_line = '\n'


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Run a game with custom parameters.",
        epilog=f'''\
Maps:
random
{new_line.join(sc2maps)}

Enemies:
random
{new_line.join(enemies.keys())}
For ingame ai, use ai.race.difficulty.

Races:
{new_line.join(races.keys())}

Difficulties:
{new_line.join(difficulty.keys())}
        ''')

    parser.add_argument("map", help="Name of the map. The script works with any map present in Starcraft 2 Maps directory.")
    parser.add_argument("enemy", help="Name of the enemy bot.")
    parser.add_argument("-p1", "--player1", help="Name of player 1 human / bot.")
    parser.add_argument("-rt", "--real-time", help="Use real-time mode.", action="store_true")
    parser.add_argument("-human", "--human", help="Human vs bot mode. Specify race with lower case")
    parser.add_argument("-release", "--release", help="Uses only release config and ignore config local", action="store_true")
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
        bot_text = get_random_enemy()

    map_name = args.map
    if map_name == "random":
        map_name = random.choice(sc2maps)

    enemy_text = args.enemy
    if enemy_text == "random":
        enemy_text = get_random_enemy()

    enemy_split: List[str] = enemy_text.split(".")
    enemy_type = enemy_split.pop(0)

    bot_split: List[str] = bot_text.split(".")
    bot_type = bot_split.pop(0)

    if bot_type not in enemies:
        print(f"Player1 type {bot_text} not found in {enemies.keys()}")
        return

    if enemy_type not in enemies:
        print(f"Enemy type {enemy_type} not found in {enemies.keys()}")
        return

    bot: AbstractPlayer = enemies[bot_type](bot_split)
    enemy: AbstractPlayer = enemies[enemy_type](enemy_split)

    folder = "games"
    if not os.path.isdir(folder):
        os.mkdir(folder)

    time = datetime.datetime.now().strftime('%Y-%m-%d %H_%M_%S')
    file_name = f'{enemy_text}_{map_name}_{time}'
    path = f'{folder}/{file_name}.log'

    handler = logging.FileHandler(path)
    root_logger.addHandler(handler)

    setup_bot(bot, bot_text, enemy_text, args)
    setup_bot(enemy, enemy_text, bot_text, args)

    run_game(
        find_map(map_name),
        [
            bot,
            enemy
        ],
        realtime=args.real_time,
        game_time_limit=(30 * 60),
        save_replay_as=f'{folder}/{file_name}.SC2Replay',
        raw_affects_selection=args.raw_selection
    )

    # release file handle
    root_logger.removeHandler(handler)
    handler.close()


def setup_bot(player: AbstractPlayer, bot_code, enemy_text: str, args):
    if isinstance(player, Bot) and hasattr(player.ai, "config"):
        my_bot: KnowledgeBot = player.ai
        my_bot.opponent_id = bot_code + "-" + enemy_text
        my_bot.run_custom = True
        if args.release:
            my_bot.config = get_config(False)


enemies = {
    # Human, must be player 1
    "human": (lambda params: Human(races[index_check(params, 0, "random")])),

    # Protoss
    "adept": (lambda params: Bot(Race.Protoss, AdeptRush())),
    "zealot": (lambda params: Bot(Race.Protoss, ProxyZealotRushBot())),
    "dt": (lambda params: Bot(Race.Protoss, DarkTemplarRush())),
    "stalker": (lambda params: Bot(Race.Protoss, MacroStalkers())),
    "4gate": (lambda params: Bot(Race.Protoss, Stalkers4Gate())),
    "robo":(lambda params: Bot(Race.Protoss, MacroRobo())),
    "voidray": (lambda params: Bot(Race.Protoss, MacroVoidray())),
    "cannonrush": (lambda params: Bot(Race.Protoss, CannonRush())),
    "randomprotoss": (lambda params: Bot(Race.Protoss, RandomProtossBot())),

    # Zerg
    "12pool": (lambda params: Bot(Race.Zerg, TwelvePool())),
    "200roach": (lambda params: Bot(Race.Zerg, MacroRoach())),
    "macro": (lambda params: Bot(Race.Zerg, MacroZergV2())),
    "lings": (lambda params: Bot(Race.Zerg, LingFlood())),
    "lingflood": (lambda params: Bot(Race.Zerg, LingFlood(False))),
    "lingspeed": (lambda params: Bot(Race.Zerg, LingFlood(True))),
    "workerrush": (lambda params: Bot(Race.Zerg, WorkerRush())),
    "hydra":(lambda params: Bot(Race.Zerg, RoachHydra())),
    "mutalisk": (lambda params: Bot(Race.Zerg, MutaliskBot())),
    "spine": (lambda params: Bot(Race.Zerg, SpineDefender())),
    "roachrush": (lambda params: Bot(Race.Zerg, RoachRush())),
    "randomzerg": (lambda params: Bot(Race.Zerg, RandomZergBot())),

    # Terran
    "marine": (lambda params: Bot(Race.Terran, MarineRushBot())),
    "cyclone": (lambda params: Bot(Race.Terran, CycloneBot())),
    "proxyrax": (lambda params: Bot(Race.Terran, ProxyRaxBot())),
    "tank": (lambda params: Bot(Race.Terran, TwoBaseTanks())),
    "reaper": (lambda params: Bot(Race.Terran, MassReaperBot())),
    "bc": (lambda params: Bot(Race.Terran, BattleCruisers())),
    "oldrusty": (lambda params: Bot(Race.Terran, Rusty())),
    "randomterran": (lambda params: Bot(Race.Terran, RandomTerranBot())),
    "bio": (lambda params: Bot(Race.Terran, BioBot())),
    "banshee": (lambda params: Bot(Race.Terran, Banshees())),

    # Random
    "weakworkerrush": (lambda params: Bot(Race.Random, WorkerRushBot())),

    # Debug
    "debugidle": (lambda params: Bot(Race.Protoss, IdleDummy())),
    "debugunits": (lambda params: Bot(Race.Zerg, DebugUnitsDummy())),
    "debugrestorepower": (lambda params: Bot(Race.Protoss, RestorePowerDummy())),
    "debuguseneural": (lambda params: Bot(Race.Zerg, UseNeuralParasiteDummy())),
    "debugdetectneural": (lambda params: Bot(Race.Protoss, DetectNeuralParasiteDummy())),

    # Built-in computer AIs
    "ai": (lambda params: Computer(races[index_check(params, 0, "random")],
                                   difficulty[index_check(params, 1, "veryhard")],
                                   builds[index_check(params, 2, "random")])),
}

races = {
    "protoss": Race.Protoss,
    "zerg": Race.Zerg,
    "terran": Race.Terran,
    "random": Race.Random,
}

builds = {
    "random": AIBuild.RandomBuild,
    "rush": AIBuild.Rush,
    "timing": AIBuild.Timing,
    "power": AIBuild.Power,
    "macro": AIBuild.Macro,
    "air": AIBuild.Air,
}

difficulty = {
    "insane": Difficulty.CheatInsane,
    "money": Difficulty.CheatMoney,
    "vision": Difficulty.CheatVision,
    "veryhard": Difficulty.VeryHard,
    "harder": Difficulty.Harder,
    "hard": Difficulty.Hard,
    "mediumhard": Difficulty.MediumHard,
    "medium": Difficulty.Medium,
    "easy": Difficulty.Easy,
    "veryeasy": Difficulty.VeryEasy,
}

sc2maps = (
    # "AbyssalReefLE",
    # "AcolyteLE",
    # "(2)RedshiftLE",
    # "(2)DreamcatcherLE",
    # "(2)LostandFoundLE",
    # "AutomatonLE",
    # "BlueshiftLE",
    # "CeruleanFallLE",
    # "DarknessSanctuaryLE",
    # "KairosJunctionLE",
    # "ParaSiteLE",
    # "PortAleksanderLE",
    # "StasisLE", # Bugged map for bots
    #"Reminiscence",
    #"PrimusQ9",
    #"Ephemeron",
    #"Sanglune",
    #"Bandwidth",
    #"Urzagol",
    #"TheTimelessVoid",
    # "CyberForestLE",
    # "KingsCoveLE",
    # "NewRepugnancyLE",
    # Season 3 2019
    "AcropolisLE",
    "DiscoBloodbathLE",
    "EphemeronLE",
    "ThunderbirdLE",
    "TritonLE",
    "WintersGateLE",
    "WorldofSleepersLE",
)


def index_check(items: list, index: int, default: str) -> str:
    try:
        return items[index]
    except IndexError:
        return default


def find_map(map_name):
    try:
        return maps.get(map_name)
    except KeyError as e:
        print(e)
        print_found_maps()
        sys.exit(1)


def print_found_maps():
    maps_folder = Paths.MAPS
    map_file_paths = glob.glob(f"{maps_folder}/**/*.SC2Map")

    print(f"\nUnique map names found from {maps_folder}...\n")

    def get_file_name(path) -> str:
        filename_w_ext = os.path.basename(path)
        filename, file_ext = os.path.splitext(filename_w_ext)
        return filename

    # Use a set to remove duplicate names (same map in multiple folders)
    map_file_names = set(map(get_file_name, map_file_paths))

    for file_name in sorted(map_file_names):
        print(file_name)


def get_random_enemy():
    filtered_enemies = list(filter(lambda key: "debug" not in key, enemies.keys()))
    return random.choice(filtered_enemies)


if __name__ == '__main__':
    main()
