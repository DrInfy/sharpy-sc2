import math
from typing import Dict

import sc2
import enum

from sc2.game_info import Ramp
from sc2.position import Point2


# Different positions for ramp
class RampPosition(enum.Enum):
    InnerEdge = 0
    Center = 1
    # Does not work correctly for ramps larger than 2
    OuterEdge = 2
    # First gate Position inside
    GateInner = 3
    # First gate Position outside
    GateOuter = 4
    # Second 3x3 building when blocking inside
    CoreInner = 5
    # Second 3x3 building when blocking outside
    CoreOuter = 6
    # When ramp is blocked Protoss style, this is where gate keeper should be
    GateZealot = 7
    # Pylon is some ways away from ramp top middle
    Away = 8
    # Between away and middle
    Between = 9
    # same as GateOuter
    GateVsProtoss = 10
    # same as CoreOuter, but room for pylon / archon instead of zealot block
    CoreVsProtoss = 11
    # use this to block adepts
    PylonBlockVsProtoss = 12

class ExtendedRamp:
    """
    Cache everything requiring any calculations from ramp
    Cache any usable positions
    """
    def __init__(self, ramp: Ramp, ai: sc2.BotAI):
        self.ramp = ramp
        # Do NOT Modify
        self.upper = list(ramp.upper2_for_ramp_wall)
        # Do NOT Modify
        self.lower = list(ramp.lower)
        self.top_center = ramp.top_center
        self.bottom_center = ramp.bottom_center
        offset = Point2((0.5,0.5))
        if self.top_center.x < self.bottom_center.x and self.top_center.y > self.bottom_center.y:
            offset = Point2((0.5,0))

        self.positions = None
        if ramp.depot_in_middle:
            self.positions: Dict[RampPosition, Point2] = {
                RampPosition.Away: ramp.depot_in_middle.towards(self.bottom_center, -5).offset(offset),
                RampPosition.Between: self.top_center.towards(self.bottom_center, -5)}
            self.find_ultimatum(ai)


    def find_ultimatum(self, ai: sc2.BotAI):
        if not self.upper:
            return
        corners = []
        for point in self.upper:
            corners.append(point)

        bottom_center = self.ramp.bottom_center # self.lower[0]
        top_center = self.ramp.top_center
        # distance2: float = None
        # for corner in corners:
        #     d = corner.distance_to(bottom_center)
        #     if upper_corner == None or d < distance2:
        #         upper_corner = corner
        #         distance2 = d

        adjust: Point2
        direction: Point2
        upper_direction: Point2
        lower_direction: Point2
        direction_gate: Point2
        upper_direction_core: Point2
        lower_direction_core: Point2
        direction_zealot: Point2

        if bottom_center.x < top_center.x and bottom_center.y < top_center.y:
            #direction = Point2((2, 1)) # Should be correnct
            direction = Point2((1.5, 0.5)) # Works correctly
            upper_direction = Point2((0, 1))
            lower_direction = Point2((2, -1))
            direction_gate = Point2((0, 0))
            direction_zealot = Point2((-0.5, -0.5))
            upper_direction_core = Point2((-2, 3))
            lower_direction_core = Point2((3, -2))
            adjust = Point2((0, 1))
        elif bottom_center.x > top_center.x and bottom_center.y < top_center.y:
            #direction = Point2((-1, 1)) # Should be correct
            direction = Point2((-1.5, 0.5)) # Works correctly
            upper_direction = Point2((1, 1))
            lower_direction = Point2((-1, -1))
            direction_gate = Point2((-1, 0))
            direction_zealot = Point2((0.5, -0.5))
            upper_direction_core = Point2((2, 3))
            lower_direction_core = Point2((-3, -2))
            adjust = Point2((0, 1))
        elif bottom_center.x < top_center.x and bottom_center.y > top_center.y:
            #direction = Point2((2, -2)) # Should be correct
            direction = Point2((1.5, -2.5)) # Works correctly
            upper_direction = Point2((2, 0))
            lower_direction = Point2((0, -2))
            direction_gate = Point2((0, -1))
            direction_zealot = Point2((-0.5, 0.5))
            upper_direction_core = Point2((3, 2))
            lower_direction_core = Point2((-2, -3))
            adjust = Point2((0, 1))
        elif bottom_center.x > top_center.x and bottom_center.y > top_center.y:
            #direction = Point2((-1, -3)) # Should be correct
            direction = Point2((-1.5, -2.5))  # Works correctly
            upper_direction = Point2((-1, 0))
            lower_direction = Point2((1, -2))
            direction_gate = Point2((-1, -1))
            direction_zealot = Point2((0.5, 0.5))
            upper_direction_core = Point2((-3, 2))
            lower_direction_core = Point2((2, -3))
            adjust = Point2((0, 1))
        else:
            print("Horizontal or vertical ramp, cannot find walling positions!")
            return

        corners.sort(key=ai.start_location.distance_to)
        inner_corner: Point2 = corners[0] + adjust
        outer_corner: Point2 = corners[1] + adjust
        inner_is_upper = inner_corner.y > outer_corner.y

        if inner_is_upper:
            self.positions[RampPosition.InnerEdge] = inner_corner.offset(upper_direction)
            self.positions[RampPosition.OuterEdge] = outer_corner.offset(lower_direction)
        else:
            self.positions[RampPosition.InnerEdge] = inner_corner.offset(lower_direction)
            self.positions[RampPosition.OuterEdge] = outer_corner.offset(upper_direction)

        self.positions[RampPosition.GateInner] = self.positions[RampPosition.InnerEdge].offset(direction_gate)
        self.positions[RampPosition.GateOuter] = self.positions[RampPosition.OuterEdge].offset(direction_gate)
        self.positions[RampPosition.GateZealot] = self.positions[RampPosition.OuterEdge].offset(direction_zealot)

        if inner_is_upper:
            self.positions[RampPosition.CoreInner] = self.positions[RampPosition.GateInner].offset(lower_direction_core)
            self.positions[RampPosition.CoreOuter] = self.positions[RampPosition.GateOuter].offset(upper_direction_core)
        else:
            self.positions[RampPosition.CoreInner] = self.positions[RampPosition.GateInner].offset(upper_direction_core)
            self.positions[RampPosition.CoreOuter] = self.positions[RampPosition.GateOuter].offset(lower_direction_core)

        self.positions[RampPosition.GateVsProtoss] = self.positions[RampPosition.GateOuter]
        self.positions[RampPosition.CoreVsProtoss] = self.positions[RampPosition.CoreOuter]

        x = self.positions[RampPosition.GateVsProtoss].x - self.positions[RampPosition.CoreVsProtoss].x
        y = self.positions[RampPosition.GateVsProtoss].y - self.positions[RampPosition.CoreVsProtoss].y
        if abs(x) == 2:
            self.positions[RampPosition.CoreVsProtoss] = self.positions[RampPosition.CoreVsProtoss].offset(Point2((math.copysign(1, x), 0)))


        if abs(y) == 2:
            self.positions[RampPosition.CoreVsProtoss] = self.positions[RampPosition.CoreVsProtoss].offset(Point2((0, math.copysign(1, y))))
        if len(self.ramp.corner_depots) == 2:
            depots = list(self.ramp.corner_depots)
            if self.positions[RampPosition.GateVsProtoss].distance_to_point2(depots[0]) < 2:
                self.positions[RampPosition.PylonBlockVsProtoss] = depots[1]
            else:
                self.positions[RampPosition.PylonBlockVsProtoss] = depots[0]

        self.positions[RampPosition.Center] = Point2(((inner_corner.x + outer_corner.x) * 0.5 + direction.x,
                           (inner_corner.y + outer_corner.y) * 0.5 + direction.y))