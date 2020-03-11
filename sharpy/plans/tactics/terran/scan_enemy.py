from typing import Optional

from sharpy.plans.acts import ActBase
from sharpy.mapping.heat_map import HeatMap
from sharpy.knowledges import Knowledge
from sc2 import UnitTypeId, AbilityId
from sc2.position import Point2
from sc2.unit import Unit


class ScanEnemy(ActBase):
    def __init__(self, interval_seconds=60):
        super().__init__()
        self.heat_map: HeatMap = None
        self.interval_seconds = interval_seconds
        self.last_scan = 0
        self.last_stealth_scan = 0
        self.stealth_interval_seconds = 15

    async def start(self, knowledge: Knowledge):
        await super().start(knowledge)
        self.heat_map = knowledge.heat_map

    async def execute(self) -> bool:
        if self.ai.time > self.last_stealth_scan + self.stealth_interval_seconds:
            stealth_hotspot = self.heat_map.get_stealth_hotspot()
            if stealth_hotspot is not None:
                await self.scan_location(self.ai, stealth_hotspot[0], True)

        if self.ai.time < self.last_scan + self.interval_seconds:
            # Normal scan on timer
            return True  # No block

        scan_target = self.solve_target()
        await self.scan_location(self.ai, scan_target, False)

        return True  # No block

    async def scan_location(self, ai, scan_target, stealth: bool):
        building: Unit
        buildings = ai.structures(UnitTypeId.ORBITALCOMMAND).ready
        for building in buildings:
            if building.energy > 50:
                if scan_target is not None:
                    self.do(building(AbilityId.SCANNERSWEEP_SCAN, scan_target))
                    if stealth:
                        self.last_stealth_scan = ai.time
                    self.last_scan = ai.time
                    return  # only one orbital should scan

    def solve_target(self) -> Optional[Point2]:
        current_zone = None
        best_score = 1
        default_score = 1000
        for zone in self.knowledge.enemy_expansion_zones:
            score = default_score + (self.ai.time - zone.last_scouted_center)
            default_score -= 100
            if score > best_score or current_zone == None:
                best_score = score
                current_zone = zone

        if current_zone is None:
            return None
        return current_zone.center_location.towards_with_random_angle(current_zone.gather_point, 4)


