import enum
import logging

import numpy as np
from typing import List

from sc2 import BotAI
from sc2.game_info import GameInfo


class MapName(enum.Enum):
    Unknown = 0
    AcolyteLE = 1
    RedshiftLE = 2
    AbyssalReefLE = 3
    DreamcatcherLE = 4
    DarknessSanctuaryLE = 5
    LostAndFoundLE = 6
    AutomatonLE = 7
    BlueshiftLE = 8
    CeruleanFallLE = 9
    KairosJunctionLE = 10
    ParaSiteLE = 11
    PortAleksanderLE = 12
    StasisLE = 13
    Reminiscence = 14
    CrystalCavern = 15


class MapInfo:
    def __init__(self, knowledge: 'Knowledge'):
        self.knowledge = knowledge
        self.ai: BotAI = knowledge.ai
        self.game_info: GameInfo = self.ai.game_info

        game_info: GameInfo = knowledge.ai.game_info
        self.zone_radiuses: List[float] = [21, 17]
        self.height_hash = np.sum(game_info.terrain_height.data_numpy)
        self.safe_first_expand = False
        self.swap_natural_with_third = False

        self.map = self.recognize_map()
        if self.map != MapName.Unknown:
            knowledge.print(f'Map recognized as {self.map.name}', type(self).__name__, stats=False)
        else:
            knowledge.print(f'Unknown map', type(self).__name__, stats=False, log_level=logging.WARNING)

    def recognize_map(self) -> MapName:

        if "Acolyte" in self.game_info.map_name: # self.height_hash == 4544808:
            self.zone_radiuses: List[float] = [24, 15]
            self.safe_first_expand = True
            return MapName.AcolyteLE
        if "Redshift" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [24, 18, 20, 18]
            self.safe_first_expand = False
            return MapName.RedshiftLE
        if "Abyssal Reef" in self.game_info.map_name:
            return MapName.AbyssalReefLE
        if "Dreamcatcher" in self.game_info.map_name:
            return MapName.DreamcatcherLE
        if "Darkness Sanctuary" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [20, 24, 24]
            return MapName.DarknessSanctuaryLE
        if "Lost and Found" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [20, 20, 20]
            return MapName.LostAndFoundLE
        if "Automaton" in self.game_info.map_name:
            return MapName.AutomatonLE
        if "Blueshift" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [24, 22]
            return MapName.BlueshiftLE
        if "Cerulean Fall" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [24, 20]
            return MapName.CeruleanFallLE
        if "Kairos Junction" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [22, 20]
            return MapName.KairosJunctionLE
        if "Para Site" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [16, 22]
            return MapName.ParaSiteLE
        if "Port Aleksander" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [24, 24]
            return MapName.PortAleksanderLE
        if "Stasis" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [24, 24]
            return MapName.StasisLE
        if "Reminiscence" in self.game_info.map_name:
            return MapName.Reminiscence
        if "Crystal Cavern" in self.game_info.map_name:
            self.zone_radiuses: List[float] = [24, 20, 24]
            return MapName.CrystalCavern

        return MapName.Unknown
