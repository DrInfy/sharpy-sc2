from typing import List

from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit, UnitOrder


class InjectLarva(ActBase):
    def __init__(self):
        super().__init__()

    async def execute(self) -> bool:
        # go through inject ready queens
        #   go through hatcheries, check if you are closest of the queens
        #       inject it
        # TODO: If no larva or running out of larva, force a queen to inject larva no matter what they're doing

        all_queens = self.ai.units(UnitTypeId.QUEEN)
        all_hatch = self.ai.townhalls.ready
        injected_halls: List[int] = []

        if all_queens.exists and all_hatch.exists:

            for queen in all_queens:  # type: Unit
                # loop all queens to see if inject larva is queued already.

                for order in queen.orders:  # type: UnitOrder
                    if order.ability.id == AbilityId.EFFECT_INJECTLARVA and type(order.target) is int:
                        injected_halls.append(order.target)
            
            idle_queens = all_queens.idle
            for queen in idle_queens:  # type: Unit
                if self.knowledge.cooldown_manager.is_ready(queen.tag, AbilityId.EFFECT_INJECTLARVA):
                    # find closest hatch
                    for town_hall in all_hatch:  # type: Unit
                        if town_hall.has_buff(BuffId.QUEENSPAWNLARVATIMER) or town_hall.tag in injected_halls:
                            continue

                        cq = all_queens.closest_to(town_hall)
                        if cq is queen:
                            self.do(queen(AbilityId.EFFECT_INJECTLARVA, town_hall))
                            injected_halls.append(town_hall.tag)
                            self.knowledge.print("injecting hatch " + str(town_hall.position), "Inject")
                            break

        return True  # Never block
