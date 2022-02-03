from sc2.data import Race
from sc2.ids.unit_typeid import UnitTypeId
from sharpy.plans.acts.act_unit import ActUnit
from sharpy.plans.acts.act_base import ActBase
from sharpy.plans.acts.workers import Workers


class AutoWorker(ActBase):
    act: ActBase

    def __init__(self, to_count=80, notready_count=8) -> None:
        super().__init__()
        self.notready_count = notready_count
        self.to_count = to_count

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        if self.knowledge.my_race == Race.Zerg:
            self.act = ActUnit(UnitTypeId.DRONE, UnitTypeId.LARVA, self.to_count, True)
        else:
            self.act = Workers(self.to_count)
        await self.start_component(self.act, knowledge)

    async def execute(self) -> bool:
        self.act.to_count = min(self.to_count, self._optimal_count())
        return await self.act.execute()

    def _optimal_count(self) -> int:
        count = 1
        for townhall in self.ai.townhalls:  # type: Unit
            if townhall.is_ready:
                count += townhall.ideal_harvesters
            else:
                count += self.notready_count
        for gas in self.ai.gas_buildings:  # type: Unit
            if gas.is_ready:
                count += gas.ideal_harvesters
            else:
                count += 3
        return count
