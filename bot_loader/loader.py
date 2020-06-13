import os
import json
from typing import Optional, List, Dict

from aiohttp import web
from .ladder_bot import BotLadder


class BotLoader:
    bots: Dict[str, BotLadder]

    def __init__(self) -> None:
        super().__init__()

    def get_bot(self, bot_name: str) -> Optional[BotLadder]:
        return self.bots.get(bot_name, None)

    def get_bots(self, path: Optional[str] = None):
        """
        Searches bot_directory_location path to find all the folders containing "ladderbots.json"
        and returns a list of bots.
        :param request:
        :return:
        """
        self.bots = dict()
        root_dir = os.path.dirname(os.path.abspath(__file__))
        if not path:
            path = os.path.join("Bots")
            path = os.path.join(root_dir, path)

        if not os.path.isdir(path):
            return

        if len(os.listdir(path)) < 1:
            return

        for x in os.listdir(path):
            full_path = os.path.join(path, x)
            json_path = os.path.join(full_path, "ladderbots.json")
            if os.path.isfile(json_path):
                bot = BotLadder(full_path, json_path)
                self.bots[bot.name] = bot
