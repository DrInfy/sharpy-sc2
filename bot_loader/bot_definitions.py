import os
from typing import List, Dict, Tuple, Callable, Optional

from .dummy_zip import DummyZip
from .ladder_zip import LadderZip
from dummies.protoss import *
from dummies.terran import *
from dummies.zerg import *
from dummies.debug import *
from sc2 import Race, AIBuild, Difficulty
from sc2.player import Human, Bot, Computer, AbstractPlayer

races = {
    "protoss": Race.Protoss,
    "zerg": Race.Zerg,
    "terran": Race.Terran,
    "random": Race.Random,
}

# Ingame AI builds

builds = {
    "random": AIBuild.RandomBuild,
    "rush": AIBuild.Rush,
    "timing": AIBuild.Timing,
    "power": AIBuild.Power,
    "macro": AIBuild.Macro,
    "air": AIBuild.Air,
}

# Ingame AI difficulty settings
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

class DummyBuilder:
    def __init__(self, key: str, name: str, race: Race, file_name: str, bot_type: type) -> None:
        self.key = key
        self.name = name
        self.race: Race = race
        self.file_name = file_name
        self.bot_type = bot_type

    def build_definition(self) -> Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]:
        race: str = self.race.name
        folder = race.lower()
        zip_builder = DummyZip(self.name, race, os.path.join("dummies", folder, self.file_name))
        return (lambda params: Bot(self.race, self.bot_type()), zip_builder)


def index_check(items: List[str], index: int, default: str) -> str:
    """
    Simple method for parsing arguments with a default value if argument index not foung
    @param items: arguments
    @param index:  index of the argument
    @param default: default value if not found
    @return: argument value or default
    """
    try:
        return items[index]
    except IndexError:
        return default


class BotDefinitions:
    def __init__(self) -> None:
        self.players: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]] = {}

    def load_zippable(self, include_bots: bool, include_dummies: bool) -> Dict[str, LadderZip]:
        self.players.clear()
        if include_bots:
            self.add_bots()
        if include_dummies:
            self.add_dummies()

        zip_dict: Dict[str, LadderZip] = {}

        for key, value in self.players.items():
            if value[1]:
                zip_dict[key] = value[1]

        return zip_dict

    def load_playable(self, include_debug: bool, include_non_bots: bool) -> Dict[str, Callable[[List[str]], AbstractPlayer]]:
        self.players.clear()
        self.add_bots()
        self.add_dummies()

        if include_debug:
            self.add_debug_bots()

        if include_non_bots:
            self.add_ai()
            self.add_human()

        play_dict: Dict[str, Callable[[List[str]], AbstractPlayer]] = {}

        for key, value in self.players.items():
            if value[0]:
                play_dict[key] = value[0]

        return play_dict

    def add_human(self):
        # Human, must be player 1
        self.players["human"] = ((lambda params: Human(races[index_check(params, 0, "random")])), None)

    def add_ai(self):
        # Human, must be player 1
        self.players["ai"] = ((lambda params: Computer(races[index_check(params, 0, "random")],
                                                       difficulty[index_check(params, 1, "veryhard")],
                                                       builds[index_check(params, 2, "random")])),
                              None)

    def add_debug_bots(self):
        """ Debug bots won't have zip function. """
        debug_bots = {
            "debugidle": (lambda params: Bot(Race.Protoss, IdleDummy())),
            "debugunits": (lambda params: Bot(Race.Zerg, DebugUnitsDummy())),
            "debugrestorepower": (lambda params: Bot(Race.Protoss, RestorePowerDummy())),
            "debuguseneural": (lambda params: Bot(Race.Zerg, UseNeuralParasiteDummy())),
            "debugdetectneural": (lambda params: Bot(Race.Protoss, DetectNeuralParasiteDummy())),
        }

        for key, func in debug_bots.items():
            self.players[key] = (func, None)

    def add_bots(self) -> None:
        """
        Override this method to add your own bots here
        """
        pass

    def add_dummies(self):
        bots: List[DummyBuilder] = [
            # Protoss
            DummyBuilder("4gate", "SharpRush", Race.Protoss, "gate4.py", Stalkers4Gate),
            DummyBuilder("adept", "SharpShades", Race.Protoss, "adept_allin.py", AdeptRush),
            DummyBuilder("cannonrush", "SharpCannons", Race.Protoss, "cannon_rush.py", CannonRush),
            DummyBuilder("disruptor", "SharpSpheres", Race.Protoss, "disruptor.py", SharpSphereBot),
            DummyBuilder("dt", "SharpShadows", Race.Protoss, "dark_templar_rush.py", DarkTemplarRush),
            DummyBuilder("robo", "SharpRobots", Race.Protoss, "robo.py", MacroRobo),
            DummyBuilder("stalker", "SharpSpiders", Race.Protoss, "macro_stalkers.py", MacroStalkers),
            DummyBuilder("voidray", "SharpRays", Race.Protoss, "voidray.py", MacroVoidray),
            DummyBuilder("zealot", "SharpKnives", Race.Protoss, "proxy_zealot_rush.py", ProxyZealotRushBot),

            # Zerg
            DummyBuilder("12pool", "BluntCheese", Race.Zerg, "twelve_pool.py", TwelvePool),
            DummyBuilder("200roach", "BluntRoaches", Race.Zerg, "macro_roach.py", MacroRoach),
            DummyBuilder("hydra", "BluntSpit", Race.Zerg, "roach_hydra.py", RoachHydra),
            DummyBuilder("lings", "BluntTeeth", Race.Zerg, "lings.py", LingFlood),
            DummyBuilder("macro", "BluntMacro", Race.Zerg, "macro_zerg_v2.py", MacroZergV2),
            DummyBuilder("mutalisk", "BluntFlies", Race.Zerg, "mutalisk.py", MutaliskBot),
            DummyBuilder("workerrush", "BluntWorkers", Race.Zerg, "worker_rush.py", WorkerRush),
            # TODO: Not really a functional bot
            # DummyBuilder("spine", "BluntDefender", Race.Zerg, "spine_defender.py", SpineDefender),
            # TODO: Not really Sharpy bot
            # DummyBuilder("roachrush", "SharpShades", Race.Zerg, "adept_allin.py", RoachRush),

            # Terran
            DummyBuilder("banshee", "RustyScreams", Race.Terran, "banshees.py", Banshees),
            DummyBuilder("bc", "FlyingRust", Race.Terran, "battle_cruisers.py", BattleCruisers),
            DummyBuilder("bio", "RustyInfantry", Race.Terran, "bio.py", BioBot),
            DummyBuilder("cyclone", "RustyLocks", Race.Terran, "cyclones.py", CycloneBot),
            DummyBuilder("marine", "RustyMarines", Race.Terran, "marine_rush.py", MarineRushBot),
            DummyBuilder("oldrusty", "OldRusty", Race.Terran, "rusty.py", Rusty),
            DummyBuilder("tank", "RustyTanks", Race.Terran, "two_base_tanks.py", TwoBaseTanks),
        ]


        for bot in bots:
            self.players[bot.key] = bot.build_definition()

        not_buildable = {
            "lingflood": (lambda params: Bot(Race.Zerg, LingFlood(False))),
            "lingspeed": (lambda params: Bot(Race.Zerg, LingFlood(True))),

            "randomzerg": (lambda params: Bot(Race.Zerg, RandomZergBot())),
            "randomprotoss": (lambda params: Bot(Race.Protoss, RandomProtossBot())),
            "randomterran": (lambda params: Bot(Race.Terran, RandomTerranBot())),
        }

        for key, func in not_buildable.items():
            # TODO: Solve this in a generic way!
            self.players[key] = (func, None)

        buildable_only = {
            "cannonrush_1": DummyZip("SharpCannonRush", "Protoss", os.path.join("dummies", "protoss", "cannon_rush.py"),
                                     "cannon_rush = 0"),
            "cannonrush_2": DummyZip("SharpCannonContain", "Protoss",
                                     os.path.join("dummies", "protoss", "cannon_rush.py"), "cannon_rush = 1"),
            "cannonrush_3": DummyZip("SharpCannonExpand", "Protoss",
                                     os.path.join("dummies", "protoss", "cannon_rush.py"), "cannon_rush = 2"),

            "marine_1": DummyZip("RustyMarines1", "Terran", os.path.join("dummies", "terran", "marine_rush.py"),
                                 "marine = 0"),
            "marine_2": DummyZip("RustyMarines2", "Terran", os.path.join("dummies", "terran", "marine_rush.py"),
                                 "marine = 1"),
            "marine_3": DummyZip("RustyMarines3", "Terran", os.path.join("dummies", "terran", "marine_rush.py"),
                                 "marine = 2"),
        }

        for key, dummy_zip in buildable_only.items():
            # TODO: Solve this in a generic way!
            self.players[key] = (None, dummy_zip)
