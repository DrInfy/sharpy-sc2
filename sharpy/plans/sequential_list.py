from typing import List

from sharpy.plans.acts import ActBase


class SequentialList(ActBase):
    def __init__(self, orders: List[ActBase]):
        assert orders is not None and isinstance(orders, list)
        super().__init__()
        for order in orders:
            assert isinstance(order, ActBase)

        self.orders: List[ActBase] = orders

    async def debug_draw(self):
        for order in self.orders:
            await order.debug_draw()
            
    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        for order in self.orders:
            await order.start(knowledge)

    async def execute(self) -> bool:
        for order in self.orders:
            result = await order.execute()
            if (not result):
                return result

        return True
