import sys
from typing import List, Optional

from sharpy.constants import Constants
from sharpy.knowledges import Knowledge
from sharpy.managers.roles import UnitTask
from sharpy.plans.acts import ActBase
from sharpy.sc2math import points_on_circumference_sorted
from sharpy.tools import IntervalFunc
from sharpy.utils import map_to_point2s_minerals
from sc2.position import Point2
from sc2.unit import Unit


class WorkerScout(ActBase):
    """
    Selects a scout worker and performs basic scout sweep across
    start and expansion locations.
    """
    def __init__(self):
        super().__init__()
        self.position_updater: IntervalFunc = None
        self.scout: Unit = None
        self.scout_tag = None

        self.enemy_ramp_top_scouted: bool = None

        # This is used for stuck / unreachable detection
        self.last_locations: List[Point2] = []

        # An ordered list of locations to scout. Current target
        # is first on the list, with descending priority, ie.
        # least important location is last.
        self.scout_locations: List[Point2] = []

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.zone_manager = knowledge.zone_manager
        self.position_updater = IntervalFunc(knowledge.ai, self.update_position, 1)

    def update_position(self):
        if self.scout:
            self.last_locations.append(self.scout.position)

    async def select_scout(self):
        workers = self.knowledge.roles.free_workers
        if not workers.exists:
            return

        if self.scout_tag is None:
            closest_worker = workers.closest_to(self.current_target)
            self.scout_tag = closest_worker.tag
            self.knowledge.roles.set_task(UnitTask.Scouting, closest_worker)

        self.scout = self.cache.by_tag(self.scout_tag)

    def distance_to_scout(self, location):
        # Return sys.maxsize so that the sort function does not crash like it does with None
        if not self.scout:
            return sys.maxsize

        if not location:
            return sys.maxsize

        return self.scout.distance_to(location)

    async def scout_locations_upkeep(self):
        if len(self.scout_locations) > 0:
            return

        enemy_base_found = self.knowledge.enemy_start_location_found

        enemy_base_scouted = enemy_base_found and self.knowledge.enemy_main_zone.is_scouted_at_least_once \
            and self.knowledge.enemy_main_zone.scout_last_circled

        enemy_base_blocked = enemy_base_found and self.enemy_ramp_top_scouted \
            and await self.target_unreachable(self.knowledge.enemy_main_zone.behind_mineral_position_center)

        if enemy_base_scouted or enemy_base_blocked:
            # When enemy found and enemy main base scouted, scout nearby expansions
            self.scout_enemy_expansions()
        elif (enemy_base_found and self.enemy_ramp_top_scouted
              and self.scout.distance_to(self.knowledge.enemy_main_zone.center_location) < 40):

            self.circle_location(self.zone_manager.enemy_main_zone.center_location)
            self.zone_manager.enemy_main_zone.scout_last_circled = self.knowledge.ai.time
        else:
            self.scout_start_locations()

    def scout_start_locations(self):
        self.print("Scouting start locations")
        self.enemy_ramp_top_scouted = False

        if self.scout:
            distance_to = self.scout.position
        else:
            distance_to = self.ai.start_location

        closest_distance = sys.maxsize
        for zone in self.zone_manager.unscouted_enemy_start_zones:
            distance = zone.center_location.distance_to(distance_to)
            # Go closest unscouted zone
            if distance < closest_distance:
                self.scout_locations.clear()

                if zone.ramp:
                    # Go ramp first
                    enemy_ramp_top_center = zone.ramp.top_center
                    self.scout_locations.append(enemy_ramp_top_center)

                # Go center of zone next
                self.scout_locations.append(zone.center_location)
                closest_distance = distance

        self.print(f"Scouting enemy base at locations {self.scout_locations}")


    def circle_location(self, location: Point2):
        self.scout_locations.clear()
        self.scout_locations = points_on_circumference_sorted(location, self.scout.position, 10, 30)
        self.print(f"Circling location {location}")

    def scout_enemy_expansions(self):
        if not self.zone_manager.enemy_start_location_found:
            return

        self.scout_locations.clear()

        self.scout_locations = map_to_point2s_minerals(self.zone_manager.enemy_expansion_zones[0:5])
        self.print(f"Scouting {len(self.scout_locations)} expansions from enemy base towards us")

    @property
    def current_target(self) -> Optional[Point2]:
        if len(self.scout_locations) > 0:
            return self.scout_locations[0]
        return None

    @property
    def current_target_is_enemy_ramp(self) -> bool:
        for zone in self.knowledge.expansion_zones: # type: Zone
            if zone.ramp and self.current_target == zone.ramp.top_center:
                return True
        return False

    async def target_unreachable(self, target) -> bool:
        if target is None:
            return False

        start = self.scout
        if (len(self.last_locations) < 5
                or self.scout.distance_to(self.last_locations[-1]) > 1
                or self.scout.distance_to(self.last_locations[-2]) > 1):
            # Worker is still moving, it's not stuck
            return False

        end = target

        result = await self.ai._client.query_pathing(start, end)
        return result is None

    def target_location_reached(self):
        if len(self.scout_locations) > 0:
            self.scout_locations.pop(0)

    async def execute(self) -> bool:
        await self.scout_locations_upkeep()
        await self.select_scout()

        if self.scout is None:
            # No one to scout
            return True  # Non blocking

        if not len(self.scout_locations):
            # Nothing to scout
            return True  # Non blocking

        self.position_updater.execute()
        dist = self.distance_to_scout(self.current_target)
        if self.current_target_is_enemy_ramp:
            if dist < Constants.SCOUT_DISTANCE_RAMP_THRESHOLD:
                self.print(f"Enemy ramp at {self.current_target} reached")
                self.target_location_reached()
                self.enemy_ramp_top_scouted = True
        else:
            if dist < Constants.SCOUT_DISTANCE_THRESHOLD:
                self.print(f"Target at {self.current_target} reached")
                self.target_location_reached()

        if await self.target_unreachable(self.current_target):
            self.print(f"target {self.current_target} unreachable!")
            self.target_location_reached()

        if self.scout is not None and self.current_target is not None:
            self.do(self.scout.move(self.current_target))

        return True  # Non blocking
