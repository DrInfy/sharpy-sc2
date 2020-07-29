import warnings
from typing import Optional

from sharpy.general.zone import Zone
from sharpy.managers.roles import UnitTask
from sc2 import UnitTypeId, Race, AbilityId, common_pb
from sc2.position import Point2
from sc2.unit import Unit, UnitOrder
from .act_base import ActBase


def get_new_townhall_type(race: Race):
    if race == Race.Zerg:
        return UnitTypeId.HATCHERY
    elif race == Race.Protoss:
        return UnitTypeId.NEXUS
    elif race == Race.Terran:
        return UnitTypeId.COMMANDCENTER


train_worker_abilitites = {AbilityId.NEXUSTRAIN_PROBE, AbilityId.COMMANDCENTERTRAIN_SCV}


class Expand(ActBase):
    def __init__(
        self,
        to_count: int,
        priority: bool = False,
        consider_worker_production: bool = True,
        priority_base_index: Optional[int] = None,
    ):
        assert isinstance(to_count, int)
        self.priority_base_index = priority_base_index
        self.to_count: int = to_count
        self.builder_tag: Optional[int] = None
        self.priority = priority
        self.consider_worker_production = consider_worker_production

        super().__init__()

    @property
    def townhall_type(self) -> UnitTypeId:
        return get_new_townhall_type(self.knowledge.my_race)

    @property
    def current_active_base_count(self) -> int:
        count = 0

        count += len(self.knowledge.our_zones_with_minerals)

        return count

    async def execute(self) -> bool:
        expand_here: "Zone" = None
        expand_now = False
        active_bases = self.current_active_base_count
        zones = self.knowledge.expansion_zones

        if self.priority_base_index is not None:
            zones = sorted(zones, key=lambda z: z.zone_index == self.priority_base_index, reverse=True)

        for zone in zones:  # type: "Zone"
            if expand_here is None and zone.should_expand_here:
                if not self.expanding_in(zone):
                    expand_here = zone
                    expand_now = zone.safe_expand_here

        if active_bases >= self.to_count:
            # We have expanded enough
            self.clear_worker()
            return True

        if expand_here is None or not self.ai.workers.exists:
            # Cannot expand
            self.clear_worker()
            return False

        worker = self.get_worker_builder(expand_here.center_location, self.builder_tag)
        pending_count = self.pending_build(self.townhall_type)

        # Inform our logic that we're looking to expand
        self.knowledge.expanding_to = expand_here

        if pending_count:
            if self.has_build_order(worker):
                self.set_worker(worker)
            else:
                self.clear_worker()

            if active_bases + pending_count >= self.to_count:
                return True

        if expand_now:
            if self.ai.can_afford(self.townhall_type):
                await self.build_expansion(expand_here)
            else:
                self.possibly_move_worker(expand_here)

            cost = self.ai.calculate_cost(self.townhall_type)
            self.knowledge.reserve(cost.minerals, cost.vespene)

        return False

    def possibly_move_worker(self, zone: Zone):
        if not self.priority:
            return
        position = zone.center_location
        worker = self.get_worker_builder(position, self.builder_tag)
        if worker is None:
            return

        d = worker.distance_to(position)
        time = d / worker.movement_speed
        available_minerals = self.ai.minerals - self.knowledge.reserved_minerals

        unit = self.ai._game_data.units[self.townhall_type.value]
        cost = self.ai._game_data.calculate_ability_cost(unit.creation_ability)

        if self.knowledge.income_calculator.mineral_income > 0 and self.consider_worker_production:
            for town_hall in self.ai.townhalls:  # type: Unit
                # TODO: Zerg(?)
                if town_hall.orders:
                    starting_next_worker_in = -50 / self.knowledge.income_calculator.mineral_income
                    for order in town_hall.orders:  # type: UnitOrder
                        if order.ability.id in train_worker_abilitites:
                            starting_next_worker_in += 12 * (1 - order.progress)

                    if starting_next_worker_in < time:
                        available_minerals -= 50  # should start producing workers soon now
                else:
                    available_minerals -= 50  # should start producing workers soon now

        if available_minerals + time * self.knowledge.income_calculator.mineral_income >= cost.minerals:
            # Go wait
            self.set_worker(worker)

            self.do(worker.move(position))

    def set_worker(self, worker: Optional[Unit]) -> bool:
        if worker:
            self.knowledge.roles.set_task(UnitTask.Building, worker)
            self.builder_tag = worker.tag
            return True

        self.builder_tag = None
        return False

    def clear_worker(self):
        if self.builder_tag is not None:
            self.knowledge.roles.clear_task(self.builder_tag)
            self.builder_tag = None

    async def build_expansion(self, expand_here: "Zone"):
        worker = self.get_worker_builder(expand_here.center_location, self.builder_tag)

        if worker is not None:
            self.print(f"Expanding to {expand_here.center_location}!")
            self.do(worker.build(self.townhall_type, expand_here.center_location))

    async def debug_actions(self):
        if self.builder_tag is not None:
            worker: Unit = self.cache.by_tag(self.builder_tag)

            if worker and worker.orders:
                moving_status = ""
                for order in worker.orders:
                    if moving_status != "":
                        moving_status += ", "
                    moving_status += order.ability.id.name
                self.client.debug_text_world(moving_status, worker.position3d)

    def expanding_in(self, zone: "Zone") -> bool:
        """ Are we already expanding to this location? """
        creation_ability: AbilityId = self.ai._game_data.units[self.townhall_type.value].creation_ability
        for worker in self.ai.workers:
            for order in worker.orders:
                if order.ability.id == creation_ability.id:
                    if isinstance(order.target, common_pb.Point) and (order.target.x, order.target.y) == (
                        zone.center_location.x,
                        zone.center_location.y,
                    ):
                        return True

        return False


class ActExpand(Expand):
    def __init__(self, to_count: int, priority: bool = False, consider_worker_production: bool = True):
        warnings.warn("'ActExpand' is deprecated, use 'Expand' instead", DeprecationWarning, 2)
        super().__init__(to_count, priority, consider_worker_production)
