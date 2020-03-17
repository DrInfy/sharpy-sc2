from math import floor
from typing import Tuple, List

from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId


class WarnBuildMacro(ActBase):
    def __init__(self, building_timings: List[Tuple[UnitTypeId, int, float]],
                 unit_timings: List[Tuple[UnitTypeId, int, float]]):
        super().__init__()

        self.building_timings = building_timings
        self.unit_timings = unit_timings

    async def execute(self) -> bool:
        if not self.debug: return True

        for item in self.building_timings:
            type_id = item[0]
            count = item[1]
            timing = item[2]

            if type_id == UnitTypeId.SUPPLYDEPOT:
                types = [UnitTypeId.SUPPLYDEPOT, UnitTypeId.SUPPLYDEPOTDROP, UnitTypeId.SUPPLYDEPOTLOWERED]
                units = self.cache.own(types)
            elif type_id == UnitTypeId.COMMANDCENTER:
                units = self.ai.townhalls
            else:
                units = self.cache.own(type_id)

            if units and len(units) == count:
                text = f'#{count} {type_id.name} started:{self.ai.time_formatted} target was {self.time_formatted(timing)}'
                await self.knowledge.chat_manager.chat_taunt_once(str(item), lambda: text)

        for item in self.unit_timings:
            type_id = item[0]
            count = item[1]
            timing = item[2]
            current_count = self.get_count(type_id, include_killed=True)
            if count == current_count:
                text = f'#{count} {type_id.name} started:{self.ai.time_formatted} target was {self.time_formatted(timing)}'
                await self.knowledge.chat_manager.chat_taunt_once(str(item), lambda: text)
        return True

    def time_formatted(self, t: float) -> str:
        """ Returns time as string in min:sec format """
        return f"{int(t // 60):02}:{int(t % 60):02}"
