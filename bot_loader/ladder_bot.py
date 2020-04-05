import subprocess
import os
from typing import Tuple, Dict

from sc2 import PlayerType, Race
from sc2.player import AbstractPlayer
import json

from sc2.portconfig import Portconfig


class BotLadder(AbstractPlayer):
    def __init__(self, path: str, ladderbots_json_path: str):
        with open(ladderbots_json_path) as f:
            data: dict = json.load(f)
        self.path = path
        bots: dict = data["Bots"]
        bot_tuple: Tuple[str, dict] = bots.popitem()
        name = bot_tuple[0]
        bot_dict: Dict[str, str] = bot_tuple[1]
        race = Race[(bot_dict["Race"])]
        super().__init__(PlayerType.Participant, race, name=name, fullscreen=False)
        self.bot_type: str = bot_dict["Type"]


    def map_type_cmd(self) -> [str]:
        bot_name = self.name
        bot_type_map = {
            "python": ["run.py", "Python"],
            "cppwin32": [f"{bot_name}.exe", "Wine"],
            "cpplinux": [f"{bot_name}", "BinaryCpp"],
            "dotnetcore": [f"{bot_name}.dll", "DotNetCore"],
            "java": [f"{bot_name}.jar", "Java"],
            "nodejs": ["main.jar", "NodeJS"],
            "Python": ["run.py", "Python"],
            "Wine": [f"{bot_name}.exe", "Wine"],
            "BinaryCpp": [f"{bot_name}", "BinaryCpp"],
            "DotNetCore": [f"{bot_name}.dll", "DotNetCore"],
            "Java": [f"{bot_name}.jar", "Java"],
            "NodeJS": ["main.jar", "NodeJS"],
        }

        mapping = bot_type_map[self.bot_type]
        file_name = mapping[0]
        # TODO: non python bots
        cmd = "python"
        return [cmd, os.path.join(self.path, file_name)]

    def __str__(self):
        if self.name is not None:
            return f"Human({self.race._name_}, name={self.name !r})"
        else:
            return f"Human({self.race._name_})"

    async def join_game(self, opponentId: str, portconfig: Portconfig):
        cmd: [str] = self.map_type_cmd()
        timeout = 1800  # 30 minutes
        start_port = str(portconfig.shared)
        game_port = str(portconfig.shared)

        print(f"game port: {start_port}")
        print(f"start port: {game_port}")
        cmd.append("--OpponentId")
        cmd.append(opponentId)
        cmd.append("--GamePort")
        cmd.append(game_port)
        cmd.append("--StartPort")
        cmd.append(start_port)

        subprocess.call(cmd, timeout=timeout)
