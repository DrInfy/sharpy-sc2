import warnings
from typing import List, Callable, Union

from sharpy.plans.require.methods import merge_to_require
from sharpy.plans.require import RequireBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class Any(RequireBase):
    """Check passes if any of the conditions are true."""

    def __init__(
        self,
        conditions: Union[RequireBase, Callable[["Knowledge"], bool], List[RequireBase]],
        *args: Union[RequireBase, Callable[["Knowledge"], bool]]
    ):
        super().__init__()

        is_act = isinstance(conditions, RequireBase) or isinstance(conditions, Callable)
        assert conditions is not None and (isinstance(conditions, list) or is_act)
        super().__init__()

        if is_act:
            self.conditions: List[RequireBase] = [merge_to_require(conditions)]
        else:
            self.conditions: List[RequireBase] = []
            for order in conditions:
                assert order is not None
                self.conditions.append(merge_to_require(order))

        for order in args:
            assert order is not None
            self.conditions.append(merge_to_require(order))

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)

        for condition in self.conditions:
            await self.start_component(condition, knowledge)

    def check(self) -> bool:
        for condition in self.conditions:
            if condition.check():
                return True

        return False


class RequiredAny(Any):
    def __init__(
        self,
        conditions: Union[RequireBase, Callable[["Knowledge"], bool], List[RequireBase]],
        *args: Union[RequireBase, Callable[["Knowledge"], bool]]
    ):
        warnings.warn("'RequiredAny' is deprecated, use 'Any' instead", DeprecationWarning, 2)
        super().__init__(conditions, *args)
