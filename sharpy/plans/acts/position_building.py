import enum
from math import floor
from typing import Optional

from sharpy.plans.acts import ActBase, DefensePosition, ActBuilding
from sharpy.general.zone import Zone
from sc2 import UnitTypeId, Race
from sc2.position import Point2


class PositionBuilding(ActBuilding):
    """Act of building buildings for mostly zerg and terran in more exact positions"""

    def __init__(
        self,
        unit_type: UnitTypeId,
        position_type: DefensePosition,
        to_base_index: Optional[int] = None,
        to_count: int = 1,
    ):
        super().__init__(unit_type, to_count)
        self.position_type = position_type
        self.to_base_index = to_base_index

    async def actually_build(self, ai, count):
        # Go through zones so that furthest expansions are fortified first
        zones = self.knowledge.expansion_zones
        for i in range(0, len(zones)):
            zone = zones[i]
            if not zone.is_ours or zone.is_under_attack:
                continue

            if self.to_base_index is not None and i != self.to_base_index:
                # Defenses are not ordered to that base
                continue

            position = self.get_position(zone)
            zone_defenses = zone.our_units(self.unit_type)
            if len(zone_defenses) >= self.to_count:
                # Already built
                continue

            can_build = True
            if self.knowledge.my_race == Race.Zerg:
                can_build = False
                int_pos = Point2((floor(position.x), floor(position.y)))
                for x in range(-2, 2):
                    for y in range(-2, 2):
                        pos = int_pos + Point2((x, y))
                        if (
                            0 < pos.x < self.ai.state.creep.width
                            and 0 < pos.y < self.ai.state.creep.height
                            and self.ai.state.creep.is_set(pos)
                        ):
                            can_build = True
                            break

            if can_build and self.knowledge.can_afford(self.unit_type):
                self.print(f"building of type {self.unit_type} near {position}")
                await self.ai.build(self.unit_type, near=position)

            self.knowledge.reserve_costs(self.unit_type)

        return False

    def get_position(self, zone: Zone) -> Point2:
        if self.position_type == DefensePosition.CenterMineralLine:
            return zone.center_location.towards(zone.behind_mineral_position_center, 4)
        if self.position_type == DefensePosition.BehindMineralLineCenter:
            return zone.behind_mineral_position_center
        if self.position_type == DefensePosition.BehindMineralLineLeft:
            return zone.behind_mineral_positions[0]
        if self.position_type == DefensePosition.BehindMineralLineRight:
            return zone.behind_mineral_positions[2]
        if self.position_type == DefensePosition.Entrance:
            return zone.center_location.towards(zone.gather_point, 5)
        if self.position_type == DefensePosition.FarEntrance:
            return zone.center_location.towards(zone.gather_point, 9)
        assert False  # Exception?
