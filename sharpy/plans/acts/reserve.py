from sc2 import UnitTypeId, BotAI, AbilityId
from sc2.unit import Unit
from .act_base import ActBase

class Reserve(ActBase):

    def __init__(self, minerals: int, gas: int):
        """

        :type minerals: int
        :type gas: int
        """
        super().__init__()
        self.gas = gas
        self.minerals = minerals

    async def execute(self) -> bool:
        self.knowledge.reserve(self.minerals, self.gas)