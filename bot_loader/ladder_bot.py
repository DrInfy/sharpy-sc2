import platform
import subprocess
import os
from typing import Tuple, Dict, Any

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
        self.file_name = bot_dict.get("FileName", None)
        super().__init__(PlayerType.Participant, race, name=name, fullscreen=False)
        self.bot_type: str = bot_dict["Type"]

    def map_type_cmd(self) -> [str]:
        bot_name = self.name
        if platform.system() == "Linux":
            # Linux
            bot_type_map = {
                "python": ["run.py", "python3.7"],
                "cppwin32": [f"{bot_name}.exe", "Wine"],
                "cpplinux": [f"{bot_name}", None],
                "dotnetcore": [f"{bot_name}.dll", "dotnet"],
                "java": [f"{bot_name}.jar", "java"],
                "Python": ["run.py", "python3.7"],
                "Wine": [f"{bot_name}.exe", None],
                "BinaryCpp": [f"{bot_name}.exe", None],
                "DotNetCore": [f"{bot_name}.dll", "dotnet"],
                "Java": [f"{bot_name}.jar", "java"],
            }
        else:
            # Windows
            bot_type_map = {
                "python": ["run.py", "python"],
                "cppwin32": [f"{bot_name}.exe", None],
                "cpplinux": [f"{bot_name}", "wsl"],
                "dotnetcore": [f"{bot_name}.dll", "dotnet"],
                "java": [f"{bot_name}.jar", "java"],
                "Python": ["run.py", "python"],
                "Wine": [f"{bot_name}.exe", None],
                "BinaryCpp": [f"{bot_name}.exe", None],
                "DotNetCore": [f"{bot_name}.dll", "dotnet"],
                "Java": [f"{bot_name}.jar", "java"],
            }

        mapping = bot_type_map[self.bot_type]
        if self.file_name:
            file_name = self.file_name
        else:
            file_name = mapping[0]
        # TODO: non python bots
        if mapping[1] is None:
            return [os.path.join(self.path, file_name)]
        if mapping[1] == "java":
            return [mapping[1], "-jar", os.path.join(self.path, file_name)]
        return [mapping[1], os.path.join(self.path, file_name)]

    def __str__(self):
        if self.name is not None:
            return f"Human({self.race._name_}, name={self.name !r})"
        else:
            return f"Human({self.race._name_})"

    async def join_game(self, opponentId: str, portconfig: Portconfig) -> Any:
        cmd: [str] = self.map_type_cmd()

        start_port = str(portconfig.shared - 1)
        game_port = str(portconfig.players[1][0])

        print(f"game port: {game_port}")
        print(f"start port: {start_port}")
        cmd.append("--OpponentId")
        cmd.append(opponentId)
        cmd.append("--GamePort")
        cmd.append(game_port)
        cmd.append("--StartPort")
        cmd.append(start_port)
        cmd.append("--LadderServer")
        cmd.append("127.0.0.1")
        print("Starting Ladder bot with command:")
        print(cmd)
        return subprocess.Popen(cmd, cwd=self.path)
