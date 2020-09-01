from typing import List, Union, Callable

from sharpy.plans.build_step import Step
from sharpy.plans.acts import ActBase

from typing import TYPE_CHECKING

from sharpy.plans.sub_acts import SubActs

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class SequentialList(SubActs):
    def __init__(
        self,
        orders: Union[
            Union[ActBase, Callable[["Knowledge"], bool]], List[Union[ActBase, Callable[["Knowledge"], bool]]]
        ],
        *argv
    ):

        super().__init__(orders, *argv)

    async def execute(self) -> bool:
        for order in self.orders:
            result = await order.execute()
            if not result:
                return result

        return True
