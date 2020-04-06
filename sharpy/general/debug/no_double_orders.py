from sharpy.plans.acts import ActBase
from sc2 import AbilityId


class NoDoubleOrders(ActBase):
    """Don't use this for terrans, seriously!"""
    def __init__(self):
        super().__init__()
        self.last_cancel = -1

    async def execute(self) -> bool:
        for unit in self.ai.structures:
            if len(unit.orders) > 1:
                msg = f'{unit.type_id} has multiple orders!'
                if self.knowledge.is_chat_allowed:
                    await self.ai.chat_send(msg)

                self.knowledge.print("[DUPLICATE] " + msg)

                if self.last_cancel + 0.2 < self.ai.time:
                    abilities = await self.ai.get_available_abilities(unit)
                    #for ability in abilities:
                    #    self.knowledge.print(f"[DUPLICATE] Ability {ability}")
                    self.knowledge.print("[DUPLICATE] " + "Cancelling!")
                    #self.do(unit(AbilityId.CANCEL_QUEUEPASIVE))
                    self.do(unit(AbilityId.CANCEL_LAST))
                    self.last_cancel = self.ai.time
        return True
