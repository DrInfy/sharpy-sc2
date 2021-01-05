import math
from typing import List, Optional, Tuple

import sc2
from sharpy.general.extended_power import ExtendedPower
from sharpy.interfaces import IUnitCache, IUnitValues
from sharpy.managers.core import ManagerBase
from sharpy.managers.core import UnitCacheManager
from sharpy.tools import IntervalFunc
from sc2.pixel_map import PixelMap
from sc2.position import Point2
from sc2.unit import Unit

SLOT_SIZE = 5


class HeatArea:
    def __init__(self, knowledge: "Knowledge", x: int, y: int, x2: int, y2: int):
        self.ai = knowledge.ai
        self.knowledge = knowledge
        self.bottom_left_x = x
        self.bottom_left_y = y
        self.top_right_x = x2
        self.top_right_y = y2
        self.center = Point2(((x + x2) / 2.0, (y + y2) / 2.0))
        self._x, self._y = self.center.rounded
        self.zone: Optional["Zone"] = None
        self.heat: float = 0
        self.stealth_heat: float = 0
        self.last_enemy_power = ExtendedPower(knowledge.unit_values)
        zone_manager = knowledge.zone_manager

        d2 = 15
        for zone in zone_manager.expansion_zones:
            if zone.center_location.distance_to(self.center) < d2:
                if self.ai.get_terrain_height(zone.center_location) == self.ai.get_terrain_height(self.center):
                    # if zone == self.zone_manager.own_main_zone:
                    #     print("MAIN ZONE")
                    self.zone = zone

    def update(self, time_change: float):
        if self.stealth_heat > 0:
            self.stealth_heat = min(2, max(0, (self.stealth_heat - time_change) * (1 - time_change * 0.5)))

        if self.heat > 0:
            if self.is_visible():
                self.heat = max(0, (self.heat - time_change * 0.02) * (1 - time_change * 0.5))
            else:
                self.heat = max(0, (self.heat - time_change * 0.01) * (1 - time_change * 0.25))

        self.heat += self.last_enemy_power.power * time_change
        self.last_enemy_power.clear()

    def is_visible(self) -> bool:
        # TODO: Check all corners?
        return self.ai.state.visibility.data_numpy[self._y, self._x] == 2


class HeatMapManager(ManagerBase):
    cache: IUnitCache
    unit_values: IUnitValues
    updater: IntervalFunc

    def __init__(self) -> None:
        super().__init__()

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        self.updater = IntervalFunc(knowledge.ai, self.__real_update, 0.5)
        self.cache = knowledge.get_required_manager(IUnitCache)
        self.init_heat_map(knowledge)

    def init_heat_map(self, knowledge: "Knowledge"):
        grid: PixelMap = knowledge.ai._game_info.placement_grid
        height = grid.height
        width = grid.width

        self.slots_w = int(math.ceil(width / SLOT_SIZE))
        self.slots_h = int(math.ceil(height / SLOT_SIZE))
        self.heat_areas: List[HeatArea] = []
        for y in range(0, self.slots_h):
            for x in range(0, self.slots_w):
                x2 = min(x * SLOT_SIZE + SLOT_SIZE, width - 1)
                y2 = min(y * SLOT_SIZE + SLOT_SIZE, height - 1)
                self.heat_areas.append(HeatArea(knowledge, x * SLOT_SIZE, y * SLOT_SIZE, x2, y2))
        self.last_update = 0
        self.last_quick_update = 0

    async def update(self):
        self.__stealth_update()
        self.updater.execute()

    async def post_update(self):
        pass

    def __stealth_update(self):
        time_change = self.ai.time - self.last_quick_update

        for unit in self.ai.all_enemy_units:  # type: Unit
            if unit.is_cloaked or unit.is_burrowed:
                own_close = self.cache.own_in_range(unit.position, 12).not_flying
                area = self.get_zone(unit.position)
                if own_close:
                    # Only add to stealth heat if we have a ground unit or building nearby
                    # Stealthed units cannot attack air
                    area.stealth_heat += 1 * time_change

    def get_zone(self, position: Point2) -> HeatArea:
        x_int = min(self.slots_w, max(0, math.floor(position.x / SLOT_SIZE)))
        y_int = min(self.slots_h, max(0, math.floor(position.y / SLOT_SIZE)))
        return self.heat_areas[x_int + y_int * self.slots_w]

    def __real_update(self):
        time_change = self.ai.time - self.last_update
        self.last_update = self.ai.time

        for unit in self.ai.enemy_units:
            area = self.get_zone(unit.position)
            area.last_enemy_power.add_unit(unit)

        for zone in self.heat_areas:
            zone.update(time_change)

    def get_stealth_hotspot(self) -> Optional[Tuple[Point2, float]]:
        top_heat_position: Point2 = None
        top_value = 0
        for heat_area in self.heat_areas:
            if heat_area.stealth_heat > top_value:
                top_heat_position = heat_area.center
                top_value = heat_area.stealth_heat

        if top_heat_position is None:
            return None

        return top_heat_position, top_value

    def get_zones_hotspot(self, zones: List["Zone"]) -> Optional[Point2]:
        top_heat_area = None
        top_value = 0
        for heat_area in self.heat_areas:
            value = heat_area.heat
            if heat_area.zone in zones and value > 0 and (top_heat_area is None or value > top_value):
                top_value = value
                top_heat_area = heat_area

        return top_heat_area
