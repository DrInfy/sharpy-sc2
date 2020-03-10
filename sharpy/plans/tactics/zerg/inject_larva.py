from typing import List

from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit


class InjectLarva(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        # go through inject ready queens
        #   go through hatcheries, check if you are closest of the queens
        #       inject it

        all_queens = self.ai.units(UnitTypeId.QUEEN)
        all_hatch = self.ai.townhalls.ready
        injected_halls: List[int] = []
        if all_queens.exists and all_hatch.exists:
            idle_queens = all_queens.idle
            for queen in idle_queens:
                if self.knowledge.cooldown_manager.is_ready(queen.tag, AbilityId.EFFECT_INJECTLARVA):
                    # find closest hatch
                    for town_hall in all_hatch:  # type: Unit
                        if town_hall.has_buff(BuffId.QUEENSPAWNLARVATIMER) or town_hall.tag in injected_halls:
                            continue

                        cq = all_queens.closest_to(town_hall)
                        if cq is queen:
                            self.do(queen(AbilityId.EFFECT_INJECTLARVA, town_hall))
                            self.knowledge.print("injecting hatch " + str(town_hall.position), "Inject")
                            break

        return True  # Never block
