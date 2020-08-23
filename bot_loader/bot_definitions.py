import os
from typing import List, Dict, Tuple, Callable, Optional

from . import BotLadder
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
    def __init__(self, key: str, name: str, race: Race, file_name: str, bot_type: type, params_count: int = 0) -> None:
        self.key = key
        self.name = name
        self.race: Race = race
        self.file_name = file_name
        self.bot_type = bot_type
        self.params_count = params_count

    def build_definition(self) -> Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]:
        race: str = self.race.name
        folder = race.lower()
        zip_builder = DummyZip(self.name, race, os.path.join("dummies", folder, self.file_name))
        if self.params_count == 0:
            return (lambda params: Bot(self.race, self.bot_type()), zip_builder)
        if self.params_count == 1:
            return (
                lambda params: Bot(self.race, self.bot_type(BotDefinitions.index_check(params, 0, "default"))),
                zip_builder,
            )
        if self.params_count == 2:
            return (
                lambda params: Bot(
                    self.race,
                    self.bot_type(
                        BotDefinitions.index_check(params, 0, "default"),
                        BotDefinitions.index_check(params, 1, "default"),
                    ),
                ),
                zip_builder,
            )
        if self.params_count == 3:
            return (
                lambda params: Bot(
                    self.race,
                    self.bot_type(
                        BotDefinitions.index_check(params, 0, "default"),
                        BotDefinitions.index_check(params, 1, "default"),
                        BotDefinitions.index_check(params, 2, "default"),
                    ),
                ),
                zip_builder,
            )


class BotDefinitions:
    def __init__(self, path: Optional[str] = None) -> None:
        self.bots: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]] = {}
        self.humans: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]] = self._human()
        self.ingame_ai: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]] = self._ai()
        self.debug_bots: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]] = {}
        self.ladder_bots: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]] = {}
        if path:
            self.ladder_bots = self._get_ladder_bots(path)

        self.add_dummies(self.bots)
        self.add_debug_bots(self.debug_bots)

    @property
    def zippable(self) -> Dict[str, LadderZip]:
        zip_dict: Dict[str, LadderZip] = {}

        for key, value in self.bots.items():
            if value[1]:
                zip_dict[key] = value[1]

        return zip_dict

    @property
    def playable(self) -> Dict[str, Callable[[List[str]], AbstractPlayer]]:
        play_dict: Dict[str, Callable[[List[str]], AbstractPlayer]] = {}

        for key, value in {**self.bots, **self.humans, **self.ladder_bots, **self.debug_bots, **self.ingame_ai}.items():
            if value[0]:
                play_dict[key] = value[0]

        return play_dict

    @property
    def random_bots(self) -> Dict[str, Callable[[List[str]], AbstractPlayer]]:
        play_dict: Dict[str, Callable[[List[str]], AbstractPlayer]] = {}

        for key, value in self.bots.items():
            if value[0]:
                play_dict[key] = value[0]

        return play_dict

    @property
    def player1(self) -> Dict[str, Callable[[List[str]], AbstractPlayer]]:
        play_dict: Dict[str, Callable[[List[str]], AbstractPlayer]] = {}

        for key, value in {**self.bots, **self.humans, **self.ingame_ai, **self.debug_bots}.items():
            if value[0]:
                play_dict[key] = value[0]

        return play_dict

    @property
    def player2(self) -> Dict[str, Callable[[List[str]], AbstractPlayer]]:
        play_dict: Dict[str, Callable[[List[str]], AbstractPlayer]] = {}

        for key, value in {**self.bots, **self.ladder_bots, **self.debug_bots, **self.ingame_ai}.items():
            if value[0]:
                play_dict[key] = value[0]

        return play_dict

    def _human(self) -> Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]]:
        # Human, must be player 1
        return {"human": ((lambda params: Human(races[BotDefinitions.index_check(params, 0, "random")])), None)}

    def _ai(self) -> Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]]:
        # Ingame ai, can be player 1 or 2 and cannot be published
        return {
            "ai": (
                (
                    lambda params: Computer(
                        races[BotDefinitions.index_check(params, 0, "random")],
                        difficulty[BotDefinitions.index_check(params, 1, "veryhard")],
                        builds[BotDefinitions.index_check(params, 2, "random")],
                    )
                ),
                None,
            )
        }

    def _get_ladder_bots(
        self, path: str = None
    ) -> Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]]:
        """
        Searches bot_directory_location path to find all the folders containing "ladderbots.json"
        and returns a list of bots.
        :param request:
        :return:
        """
        bots = dict()

        if not os.path.isdir(path):
            return bots

        if len(os.listdir(path)) < 1:
            return bots

        for x in os.listdir(path):
            full_path = os.path.join(path, x)
            json_path = os.path.join(full_path, "ladderbots.json")
            if os.path.isfile(json_path):
                key = os.path.basename(os.path.normpath(full_path))
                bots[key] = (lambda params, tmp_path=full_path, path2=json_path: BotLadder(tmp_path, path2), None)
        return bots

    def add_debug_bots(self, bot_dict: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]]):
        """ Debug bots won't have zip function. """
        debug_bots = {
            "debugidle": (lambda params: Bot(Race.Protoss, IdleDummy())),
            "debugunits": (lambda params: Bot(Race.Zerg, DebugUnitsDummy())),
            "debugrestorepower": (lambda params: Bot(Race.Protoss, RestorePowerDummy())),
            "debuguseneural": (lambda params: Bot(Race.Zerg, UseNeuralParasiteDummy())),
            "debugdetectneural": (lambda params: Bot(Race.Protoss, DetectNeuralParasiteDummy())),
            "debugexpanddummy": (lambda params: Bot(Race.Zerg, ExpandDummy())),
        }

        for key, func in debug_bots.items():
            bot_dict[key] = (func, None)

    def add_bot(
        self, key: str, func: Callable[[List[str]], AbstractPlayer], ladder_zip: Optional[LadderZip] = None
    ) -> None:
        """
        Add your own custom bots here
        """
        assert isinstance(key, str)
        assert isinstance(func, Callable)
        assert ladder_zip is None or isinstance(ladder_zip, LadderZip)
        self.bots[key] = (func, ladder_zip)

    @staticmethod
    def index_check(items: List[str], index: int, default: Optional[str]) -> str:
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

    def add_dummies(self, bot_dict: Dict[str, Tuple[Callable[[List[str]], AbstractPlayer], Optional[LadderZip]]]):
        bots: List[DummyBuilder] = [
            # Protoss
            DummyBuilder("4gate", "SharpRush", Race.Protoss, "gate4.py", Stalkers4Gate),
            DummyBuilder("adept", "SharpShades", Race.Protoss, "adept_allin.py", AdeptRush),
            DummyBuilder("cannonrush", "SharpCannons", Race.Protoss, "cannon_rush.py", CannonRush, params_count=1),
            DummyBuilder("disruptor", "SharpSpheres", Race.Protoss, "disruptor.py", SharpSphereBot),
            DummyBuilder("dt", "SharpShadows", Race.Protoss, "dark_templar_rush.py", DarkTemplarRush),
            DummyBuilder("robo", "SharpRobots", Race.Protoss, "robo.py", MacroRobo),
            DummyBuilder("stalker", "SharpSpiders", Race.Protoss, "macro_stalkers.py", MacroStalkers),
            DummyBuilder("voidray", "SharpRays", Race.Protoss, "voidray.py", MacroVoidray),
            DummyBuilder("zealot", "SharpKnives", Race.Protoss, "proxy_zealot_rush.py", ProxyZealotRushBot),
            DummyBuilder("tempest", "SharpTempests", Race.Protoss, "one_base_tempests.py", OneBaseTempests),
            # Zerg
            DummyBuilder("12pool", "BluntCheese", Race.Zerg, "twelve_pool.py", TwelvePool),
            DummyBuilder("200roach", "BluntRoaches", Race.Zerg, "macro_roach.py", MacroRoach),
            DummyBuilder("hydra", "BluntSpit", Race.Zerg, "roach_hydra.py", RoachHydra),
            DummyBuilder("lings", "BluntTeeth", Race.Zerg, "lings.py", LingFlood),
            DummyBuilder("macro", "BluntMacro", Race.Zerg, "macro_zerg_v2.py", MacroZergV2),
            DummyBuilder("mutalisk", "BluntFlies", Race.Zerg, "mutalisk.py", MutaliskBot),
            DummyBuilder("workerrush", "BluntWorkers", Race.Zerg, "worker_rush.py", WorkerRush),
            DummyBuilder("lurker", "BluntLurkers", Race.Zerg, "lurkers.py", LurkerBot),
            # TODO: Not really a functional bot
            # DummyBuilder("spine", "BluntDefender", Race.Zerg, "spine_defender.py", SpineDefender),
            # TODO: Not really Sharpy bot
            # DummyBuilder("roachrush", "SharpShades", Race.Zerg, "adept_allin.py", RoachRush),
            # Terran
            DummyBuilder("banshee", "RustyScreams", Race.Terran, "banshees.py", Banshees),
            DummyBuilder("bc", "FlyingRust", Race.Terran, "battle_cruisers.py", BattleCruisers, params_count=1),
            DummyBuilder("bio", "RustyInfantry", Race.Terran, "bio.py", BioBot),
            DummyBuilder("cyclone", "RustyLocks", Race.Terran, "cyclones.py", CycloneBot),
            DummyBuilder("marine", "RustyMarines", Race.Terran, "marine_rush.py", MarineRushBot, params_count=1),
            DummyBuilder("oldrusty", "OldRusty", Race.Terran, "rusty.py", Rusty),
            DummyBuilder("tank", "RustyTanks", Race.Terran, "two_base_tanks.py", TwoBaseTanks),
            DummyBuilder("terranturtle", "RustyOneBaseTurtle", Race.Terran, "one_base_turtle.py", OneBaseTurtle),
            DummyBuilder("saferaven", "SafeRaven", Race.Terran, "safe_tvt_raven.py", TerranSafeTvT),
        ]

        for bot in bots:
            bot_dict[bot.key] = bot.build_definition()

        not_buildable = {
            "lingflood": (lambda params: Bot(Race.Zerg, LingFlood(False))),
            "lingspeed": (lambda params: Bot(Race.Zerg, LingFlood(True))),
            "randomzerg": (lambda params: Bot(Race.Zerg, RandomZergBot())),
            "randomprotoss": (lambda params: Bot(Race.Protoss, RandomProtossBot())),
            "randomterran": (lambda params: Bot(Race.Terran, RandomTerranBot())),
        }

        for key, func in not_buildable.items():
            # TODO: Solve this in a generic way!
            bot_dict[key] = (func, None)

        buildable_only = {
            "cannonrush_1": DummyZip(
                "SharpCannonRush", "Protoss", os.path.join("dummies", "protoss", "cannon_rush.py"), "cannonrush = 0"
            ),
            "cannonrush_2": DummyZip(
                "SharpCannonContain", "Protoss", os.path.join("dummies", "protoss", "cannon_rush.py"), "cannonrush = 1"
            ),
            "cannonrush_3": DummyZip(
                "SharpCannonExpand", "Protoss", os.path.join("dummies", "protoss", "cannon_rush.py"), "cannonrush = 2"
            ),
            "marine_1": DummyZip(
                "RustyMarines1", "Terran", os.path.join("dummies", "terran", "marine_rush.py"), "marine = 0"
            ),
            "marine_2": DummyZip(
                "RustyMarines2", "Terran", os.path.join("dummies", "terran", "marine_rush.py"), "marine = 1"
            ),
            "marine_3": DummyZip(
                "RustyMarines3", "Terran", os.path.join("dummies", "terran", "marine_rush.py"), "marine = 2"
            ),
            "bcjump": DummyZip(
                "FlyingRustJump", "Terran", os.path.join("dummies", "terran", "battle_cruisers.py"), "bc = 1"
            ),
        }

        for key, dummy_zip in buildable_only.items():
            # TODO: Solve this in a generic way!
            bot_dict[key] = (None, dummy_zip)
