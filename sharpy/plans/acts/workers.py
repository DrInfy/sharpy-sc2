import math

from sharpy.knowledges import Knowledge
from sharpy.plans.acts import ActBase
from sc2 import UnitTypeId, AbilityId, Race
from sc2.game_data import AbilityData, Cost
from sc2.unit import Unit, UnitOrder


class Workers(ActBase):

    """
    Builds workers in an optimal way for Protoss and Terran.
    Does not function for Zerg!
    Does not consider chrono boost.
    """

    def __init__(self, to_count: int = 80):
        super().__init__()
        self.unit_type: UnitTypeId = None
        self.to_count = to_count
        self.ability: AbilityId = None
        self.cost: Cost = None
        self.supply_building: UnitTypeId = None
        self.supply_build_time: int = None

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        assert knowledge.my_worker_type in {UnitTypeId.PROBE, UnitTypeId.SCV}
        self.unit_type = knowledge.my_worker_type
        unit_data = self.ai._game_data.units[self.unit_type.value]
        ability_data: AbilityData = unit_data.creation_ability
        self.ability = ability_data.id
        self.cost = ability_data.cost
        if self.knowledge.my_race == Race.Protoss:
            self.supply_building = UnitTypeId.PYLON
            self.supply_build_time = 18
        elif self.knowledge.my_race == Race.Terran:
            self.supply_building = UnitTypeId.SUPPLYDEPOT
            self.supply_build_time = 21

    async def execute(self) -> bool:
        builders = self.ai.townhalls.ready
        simultaneous_count = len(builders)
        count = self.ai.supply_workers  # Current count
        pending_count = self.unit_pending_count(self.unit_type)
        count = count + pending_count  # Total count

        if count >= self.to_count:
            return True

        need_count_more = self.to_count - count

        simultaneous_count = min(simultaneous_count, need_count_more)

        available_builders = builders.idle
        busy_builders = builders.tags_not_in(available_builders.tags)

        supply_for = self.ai.supply_left

        income = self.knowledge.income_calculator.mineral_income
        if income == 0:
            income = 0.01  # to prevent division by zero exceptions

        if supply_for < simultaneous_count:
            unfinished = self.cache.own(self.supply_building).not_ready

            if not unfinished:
                # Don't reserve minerals when we won't have supply to build more
                simultaneous_count = supply_for
            else:
                progress = 0
                need_new_supply_for = simultaneous_count - supply_for

                for supply_building in unfinished:  # type: Unit
                    if supply_building.build_progress > progress:
                        progress = supply_building.build_progress

                time_until_ready = (1 - progress) * self.supply_build_time

                if time_until_ready > need_new_supply_for * self.cost.minerals / income:
                    # There's still enough time to get enough minerals before next supply building is ready
                    simultaneous_count -= need_new_supply_for

        if simultaneous_count > len(available_builders):
            time_to_reserve = self.cost.minerals / income
            percentage_to_reserve = (12 - time_to_reserve) / 12

            # Let's check our income for busy builders
            for builder in busy_builders:  # type: Unit
                if builder.orders:
                    order: UnitOrder = builder.orders[0]
                    if order.ability.id == self.ability and order.progress > percentage_to_reserve:
                        self.knowledge.reserve(self.cost.minerals, self.cost.vespene)
                        simultaneous_count -= 1
                        if simultaneous_count <= len(available_builders):
                            break

        for builder in available_builders:
            if not builder.is_flying and self.allow_new_action(builder):
                if self.knowledge.cooldown_manager.is_ready(builder.tag, self.ability):
                    self.print(f"{self.unit_type.name} from {builder.type_id.name} at {builder.position}")
                    self.knowledge.reserve(self.cost.minerals, self.cost.vespene)
                    self.do(builder.train(self.unit_type))

        return False
