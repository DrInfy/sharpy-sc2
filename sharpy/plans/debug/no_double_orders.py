from sc2.ids.ability_id import AbilityId
from sharpy.plans.acts import ActBase


class NoDoubleOrders(ActBase):
    """Don't use this for terrans, seriously!"""

    def __init__(self):
        super().__init__()
        self.last_cancel = -1

    async def execute(self) -> bool:
        for unit in self.ai.structures:
            if len(unit.orders) > 1:
                msg = f"{unit.type_id} has multiple orders!"

                self.knowledge.print("[DUPLICATE] " + msg)

                if self.last_cancel + 0.2 < self.ai.time:
                    self.knowledge.print("[DUPLICATE] " + "Cancelling!")
                    unit(AbilityId.CANCEL_LAST)
                    self.last_cancel = self.ai.time
        return True
