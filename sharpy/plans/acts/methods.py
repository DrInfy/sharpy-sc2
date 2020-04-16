from typing import Optional, Union, Callable

from sharpy.plans.acts.act_base import ActBase
from sharpy.plans.acts.act_custom import ActCustom
from sharpy.plans.require.require_custom import RequireCustom
from sharpy.plans.require.require_base import RequireBase
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


def merge_to_act(obj: Optional[Union[ActBase, Callable[["Knowledge"], bool]]]) -> Optional[ActBase]:
    if isinstance(obj, ActBase) or obj is None:
        return obj
    assert isinstance(obj, Callable)
    return ActCustom(obj)


def merge_to_require(obj: Optional[Union[RequireBase, Callable[["Knowledge"], bool]]]) -> Optional[RequireBase]:
    if isinstance(obj, RequireBase) or obj is None:
        return obj
    assert isinstance(obj, Callable)
    return RequireCustom(obj)
