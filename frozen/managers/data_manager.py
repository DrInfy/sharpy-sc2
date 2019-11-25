import json
import os
from uuid import uuid4

import jsonpickle
from datetime import datetime
from pathlib import Path

from sc2 import Result

from frozen.managers.manager_base import ManagerBase
from frozen.tools import IntervalFunc
from frozen.tools.opponent_data import GameResult, OpponentData

DATA_FOLDER = "data"

class DataManager(ManagerBase):
    data: OpponentData
    enabled: bool
    enable_write: bool

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.enabled = self.ai.opponent_id is not None
        self.enable_write = self.knowledge.config["general"].getboolean("write_data")
        self.file_name = DATA_FOLDER + os.sep + str(self.ai.opponent_id) + ".json"

        self.updater = IntervalFunc(self.ai, lambda: self.real_update(), 1)
        self.result = GameResult()
        self.result.enemy_race = knowledge.enemy_race

        if self.enabled:
            self.result.game_started = datetime.now().isoformat()
            my_file = Path(self.file_name)
            if my_file.is_file():
                try:
                    with open(self.file_name, 'r') as handle:
                        text = handle.read()
                        self.data = jsonpickle.decode(text)

                except:
                    self.data = OpponentData()
                    self.data.enemy_id = self.ai.opponent_id
                    self.knowledge.print("Data read failed on game start.")
            else:
                self.data = OpponentData()
                self.data.enemy_id = self.ai.opponent_id

    async def update(self):
        pass

    async def post_update(self):
        if self.enabled:
            self.updater.execute()

    def real_update(self):
        if self.result.first_attacked is None:
            for zone in self.knowledge.expansion_zones:
                if zone.is_ours and zone.known_enemy_power.power > 10:
                    self.result.first_attacked = self.ai.time

        # Pre emptive write in case on end does not trigger properly
        if self.result.result != 1 and self.knowledge.game_analyzer.predicting_victory:
            self.write_victory()
        elif self.result.result != -1 and self.knowledge.game_analyzer.predicting_defeat:
            self.write_defeat()

    def set_build(self, build_name: str):
        self.result.build_used = build_name

    def write_defeat(self):
        self.result.result = -1
        self.result.game_duration = self.ai.time
        self.write_results()

    def write_victory(self):
        self.result.result = 1
        self.result.game_duration = self.ai.time
        self.write_results()

    def write_results(self):
        if not self.enable_write:
            return
        my_file = Path(self.file_name)

        if my_file.is_file():
            try:
                with open(self.file_name, 'r') as handle:
                    text = handle.read()
                    self.data = jsonpickle.decode(text)
            except:
                # Don't write if we can't read the current data
                self.knowledge.print("Data read failed on save.")
                return
        elif not os.path.exists(DATA_FOLDER):
            os.makedirs(DATA_FOLDER)

        to_remove = None
        for result in self.data.results:
            if result.guid == self.result.guid:
                to_remove = result
                break

        if to_remove:
            self.data.results.remove(to_remove)

        self.data.results.append(self.result)

        frozen = jsonpickle.encode(self.data)
        try:
            with open(self.file_name, 'w') as handle:
                handle.write(frozen)
                # pickle.dump(self.data, handle, protocol=pickle.HIGHEST_PROTOCOL)
        except:
            self.knowledge.print("Data write failed.")

    async def on_end(self, game_result: Result):
        if not self.enabled:
            return
        
        if game_result == Result.Victory:
            self.result.result = 1
        elif game_result == Result.Tie:
            self.result.result = 0
        elif game_result == Result.Defeat:
            self.result.result = -1

        self.result.game_duration = self.ai.time
        self.write_results()
