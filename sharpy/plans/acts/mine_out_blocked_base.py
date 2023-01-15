from typing import List

from sc2.units import Units
from sharpy.managers.core.roles import UnitTask
from sharpy.plans.acts import ActBase


"""
This act is mostly to fix StargazersAIE mineral blocking certain bases
"""


class MineOpenBlockedBase(ActBase):

    zones_needing_help: List[int]
    worker_tags: List[int] = []

    def __init__(self, units_to_clear: int = 1):
        self.units_to_clear = units_to_clear
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.zones_needing_help = []
        self.worker_tags: List[int] = []

        for zone in self.zone_manager.expansion_zones:
            if self.ai.mineral_field.closer_than(4, zone.center_location).amount > 0:
                self.zones_needing_help.append(zone.zone_index)

    def end_act(self) -> bool:
        if self.worker_tags:
            self.roles.clear_tasks(self.cache.by_tags(self.worker_tags))
            self.worker_tags.clear()
        return True

    async def execute(self) -> bool:
        if len(self.zones_needing_help) == 0 or len(self.ai.workers) < 5:
            return True

        help_zone_index = -1

        for index in range(0, len(self.zone_manager.expansion_zones)):
            if (
                self.zone_manager.expansion_zones[index].has_minerals
                and not self.zone_manager.expansion_zones[index].is_ours
            ):
                if index in self.zones_needing_help:
                    help_zone_index = index
                break

        if help_zone_index < 0:
            return self.end_act()

        zone = self.zone_manager.expansion_zones[help_zone_index]
        mineral_fields = self.ai.mineral_field.closer_than(4, zone.center_location)

        if len(mineral_fields) == 0:
            return self.end_act()

        if self.worker_tags:
            workers = self.cache.by_tags(self.worker_tags)
        else:
            workers = Units([], self.ai)

        while len(workers) < self.units_to_clear:
            free_workers = self.roles.free_workers
            if free_workers.exists:
                workers.append(free_workers.closest_to(mineral_fields.center))
            else:
                break

        mineral_tags = mineral_fields.tags
        self.worker_tags.clear()

        for worker in workers:
            if worker.order_target not in mineral_tags and not worker.is_returning:
                worker.smart(mineral_fields.first)
            self.roles.set_task(UnitTask.Reserved, worker)
            self.worker_tags.append(worker.tag)

        return True  # Non blocking
