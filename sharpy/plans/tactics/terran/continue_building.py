import sc2
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId
from sc2.unit import Unit

REACTORS = {UnitTypeId.BARRACKSREACTOR, UnitTypeId.FACTORYREACTOR,
            UnitTypeId.STARPORTREACTOR, UnitTypeId.REACTOR}
TECHLABS = {UnitTypeId.BARRACKSTECHLAB, UnitTypeId.FACTORYTECHLAB,
            UnitTypeId.STARPORTTECHLAB, UnitTypeId.TECHLAB}
TECHLABS_AND_REACTORS = REACTORS.union(TECHLABS)

class ContinueBuilding(ActBase):
    async def execute(self) -> bool:
        building: Unit
        buildings = self.ai.structures.not_ready.exclude_type(TECHLABS_AND_REACTORS)
        scv_constructing = self.ai.units.filter(lambda unit: unit.is_constructing_scv)

        if buildings.amount > scv_constructing.amount:
            for building in buildings:
                if (self.knowledge.unit_values.build_time(building.type_id) > 0
                        and not scv_constructing.closer_than(building.radius+0.5, building)):

                    self.knowledge.print(f"[Building continue] {building.type_id} {building.position}")
                    workers = self.knowledge.roles.free_workers()
                    if workers.exists:
                        scv = workers.closest_to(building)
                        self.do(scv(AbilityId.SMART, building))
        return True
