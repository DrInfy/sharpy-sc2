from typing import Callable, Union

from sharpy.plans.require.methods import merge_to_require
from sharpy.plans.require import RequireBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class Once(RequireBase):
    """Check passes if condition has ever been true."""

    def __init__(self, condition: Union[RequireBase, Callable[["Knowledge"], bool]]):
        super().__init__()

        assert isinstance(condition, RequireBase) or isinstance(condition, Callable)

        self.condition = merge_to_require(condition)
        self.triggered = False

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        await self.start_component(self.condition, knowledge)

    def check(self) -> bool:
        if self.triggered:
            return True

        if self.condition.check():
            self.triggered = True
            return True

        return False
