from typing import List, Union, Callable

from sharpy.plans.build_step import Step
from sharpy.plans.acts import ActBase

from typing import TYPE_CHECKING

from sharpy.plans.acts import merge_to_act

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class SubActs(ActBase):
    def __init__(
        self,
        orders: Union[
            Union[ActBase, Callable[["Knowledge"], bool]], List[Union[ActBase, Callable[["Knowledge"], bool]]]
        ],
        *argv: Union[ActBase, Callable[["Knowledge"], bool]],
    ):

        is_act = isinstance(orders, ActBase) or isinstance(orders, Callable)
        assert orders is not None and (isinstance(orders, list) or is_act)
        super().__init__()

        if is_act:
            self.orders: List[ActBase] = [merge_to_act(orders)]
        else:
            self.orders: List[ActBase] = []
            for order in orders:
                assert order is not None
                self.orders.append(merge_to_act(order))

        for order in argv:
            assert order is not None
            self.orders.append(merge_to_act(order))

    async def debug_draw(self):
        for order in self.orders:
            await order.debug_draw()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        for order in self.orders:
            await self.start_component(order, knowledge)
