from typing import List

import sc2

#from sharpy import 'Knowledge'
from .act_base import ActBase

class ActMany(ActBase):
    # Act of building multiple units
    def __init__(self, acts: List[ActBase]):
        assert acts is not None and isinstance(acts, list)
        self.acts = acts
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        for act in self.acts:
            await act.start(knowledge)

    async def execute(self) -> bool:
        result = True
        for act in self.acts:
            result &= await act.execute()
        return result
