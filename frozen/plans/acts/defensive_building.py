import enum
from math import floor
from typing import Optional

from frozen.plans.acts import ActBase
from frozen.general.zone import Zone
from sc2 import UnitTypeId, Race
from sc2.position import Point2


class DefensePosition(enum.Enum):
    CenterMineralLine = 0
    BehindMineralLineCenter = 1
    BehindMineralLineLeft = 2
    BehindMineralLineRight = 3
    Entrance = 4


class DefensiveBuilding(ActBase):
    """Act of building defensive buildings for zerg and terran, does not work with protoss due to pylon requirement!"""

    def __init__(self, unit_type: UnitTypeId, position_type: DefensePosition, to_base_index: Optional[int] = None):
        super().__init__()
        self.unit_type = unit_type
        self.position_type = position_type
        self.to_base_index = to_base_index

    async def execute(self) -> bool:
        map_center = self.ai.game_info.map_center
        is_done = True
        pending_defense_count = self.pending_build(self.unit_type)
        if pending_defense_count > 0:
            return True
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
            if zone_defenses.exists and zone_defenses.closest_distance_to(position) < 6:
                # Already built
                continue

            can_build = True
            if self.knowledge.my_race == Race.Zerg:
                can_build = False
                int_pos = Point2((floor(position.x), floor(position.y)))
                for x in range(-2, 2):
                    for y in range(-2, 2):
                        pos = int_pos + Point2((x, y))
                        if pos.x > 0 and pos.x < self.ai.state.creep.width and \
                                pos.y > 0 and pos.y < self.ai.state.creep.height and \
                                self.ai.state.creep.is_set(pos):
                            can_build = True
                            break


            if can_build and self.knowledge.can_afford(self.unit_type):
                self.knowledge.print(f'[DefensiveBuilding] building of type {self.unit_type} near {position}')
                await self.ai.build(self.unit_type, near=position)
            else:
                is_done = False
            self.knowledge.reserve_costs(self.unit_type)

        return is_done

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
        assert False # Exception?
