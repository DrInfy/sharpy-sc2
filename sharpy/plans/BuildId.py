from typing import Union
from sc2 import UnitTypeId, Race
from sc2.constants import ALL_GAS
from sharpy.managers.unit_value import buildings_5x5, buildings_3x3, buildings_2x2, BUILDING_IDS
from sharpy.plans.acts import ActBase, GridBuilding, Expand, Workers, BuildGas
from sharpy.plans.acts.protoss import ProtossUnit
from sharpy.plans.acts.terran import TerranUnit
from sharpy.plans.acts.zerg import ZergUnit


class BuildId(ActBase):
    act: ActBase

    def __init__(self, type_id: Union[UnitTypeId, int], to_count: int, priority: bool = True) -> None:
        if type_id is int:
            self.type_id = UnitTypeId[type_id]
        else:
            self.type_id = type_id

        self.to_count = to_count
        self.priority = priority

        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        if self.type_id in {UnitTypeId.PROBE, UnitTypeId.SCV}:
            self.act = Workers(self.to_count)
        elif self.type_id in ALL_GAS:
            self.act = BuildGas(self.to_count)
        elif self.type_id in buildings_5x5:
            self.act = Expand(self.to_count, priority=self.priority, consider_worker_production=False)
        elif self.type_id in BUILDING_IDS:
            self.act = GridBuilding(
                self.type_id, self.to_count, priority=self.priority, consider_worker_production=False
            )
        else:
            if self.ai.race == Race.Protoss:
                self.act = ProtossUnit(self.type_id, self.to_count, priority=self.priority, only_once=True)
            elif self.ai.race == Race.Terran:
                self.act = TerranUnit(self.type_id, self.to_count, priority=self.priority, only_once=True)
            else:
                self.act = ZergUnit(self.type_id, self.to_count, priority=self.priority, only_once=True)

        await self.act.start(knowledge)

    async def execute(self) -> bool:
        # I promise this works and you can ignore any warnings
        self.act.to_count = self.to_count
        return await self.act.execute()
