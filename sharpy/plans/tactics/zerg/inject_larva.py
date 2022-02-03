from typing import List

from sc2.ids.ability_id import AbilityId
from sharpy.managers.core.roles import UnitTask
from sharpy.plans.acts import ActBase
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit, UnitOrder


class InjectLarva(ActBase):
    """
    When using force_inject_on_larva, use the following in KnowledgeBot:
    self.roles.set_tag_each_iteration = True

    @param force_inject_on_larva how many larva until we force a queen to inject a townhall, set to negative for never.
    """

    def __init__(self, force_inject_on_larva: int = -1):
        super().__init__()
        self.force_inject_on_larva = force_inject_on_larva

    async def execute(self) -> bool:
        # go through inject ready queens
        #   go through hatcheries, check if you are closest of the queens
        #       inject it
        all_queens = self.ai.units(UnitTypeId.QUEEN)
        if all_queens.empty:
            return True  # Never block

        larvas = self.cache.own(UnitTypeId.LARVA)
        force_inject = len(larvas) <= self.force_inject_on_larva

        all_hatch = self.ai.townhalls.ready
        injected_halls: List[int] = []

        if all_queens.exists and all_hatch.exists:

            for queen in all_queens:  # type: Unit
                # loop all queens to see if inject larva is queued already.

                for order in queen.orders:  # type: UnitOrder
                    if order.ability.id == AbilityId.EFFECT_INJECTLARVA and type(order.target) is int:
                        if force_inject:
                            self.roles.set_task(UnitTask.Reserved, queen)

                        injected_halls.append(order.target)

            if force_inject:
                usable_queens = self.roles.get_types_from(
                    {UnitTypeId.QUEEN}, UnitTask.Idle, UnitTask.Fighting, UnitTask.Defending
                )
            else:
                usable_queens = all_queens.idle

            for queen in usable_queens:  # type: Unit
                if self.knowledge.cooldown_manager.is_ready(queen.tag, AbilityId.EFFECT_INJECTLARVA):
                    # find closest hatch
                    for town_hall in all_hatch:  # type: Unit
                        if town_hall.has_buff(BuffId.QUEENSPAWNLARVATIMER) or town_hall.tag in injected_halls:
                            continue

                        cq = all_queens.closest_to(town_hall)
                        if cq is queen:
                            queen(AbilityId.EFFECT_INJECTLARVA, town_hall)
                            if force_inject:
                                self.roles.set_task(UnitTask.Reserved, queen)
                            injected_halls.append(town_hall.tag)
                            self.knowledge.print("injecting hatch " + str(town_hall.position), "Inject")
                            break

        return True  # Never block

    async def debug_actions(self):
        for queen in self.cache.own(UnitTypeId.QUEEN):
            if queen.orders:
                self.debug_text_on_unit(queen, queen.orders[0].ability.id.name)
