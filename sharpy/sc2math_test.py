from sc2.position import Point2

from sharpy.managers import UnitValue
from .sc2math import points_on_circumference, points_on_circumference_sorted
from sc2 import UnitTypeId

unit_values = UnitValue()


class TestMath:
    def test_building_start_time_returns_start_time(self):
        game_time = 40
        build_progress = 0.46
        type_id = UnitTypeId.SPAWNINGPOOL
        start_time = unit_values.building_start_time(game_time, type_id, build_progress)

        assert start_time == 18.84

    def test_building_start_time_does_not_crash_with_unknown_type_id(self):
        game_time = 40
        build_progress = 0.46
        type_id = UnitTypeId.KERRIGANEGG

        try:
            start_time = unit_values.building_start_time(game_time, type_id, build_progress)
        except:
            assert False

    def test_building_completion_time_works(self):
        game_time = 40
        build_progress = 0.46
        type_id = UnitTypeId.SPAWNINGPOOL

        completion_time = unit_values.building_completion_time(game_time, type_id, build_progress)

        assert completion_time == 18.84 + unit_values.build_time(type_id)

    def test_building_completion_time_does_not_crash_with_unknown_type_id(self):
        game_time = 40
        build_progress = 0.46
        type_id = UnitTypeId.KERRIGANEGG

        try:
            completion_time = unit_values.building_completion_time(game_time, type_id, build_progress)
        except:
            assert False

    def test_points_on_circumference_with_unit_circle(self):
        center = Point2((0, 0))
        radius = 1
        n = 4

        points = points_on_circumference(center, radius, n)

        assert len(points) == n
        # Points start from the "right side" of the circle
        assert points[0] == Point2((1, 0))
        assert points[1] == Point2((0, 1))
        assert points[2] == Point2((-1, 0))
        assert points[3] == Point2((0, -1))

    def test_points_on_circumference_sorted_with_unit_circle(self):
        center = Point2((0, 0))
        closest_to = Point2((0, 10))
        radius = 1
        n = 4

        points = points_on_circumference_sorted(center, closest_to, radius, n)

        assert len(points) == n
        # Points should be sorted so that first item has shortest distance to
        # closest_to parameter
        assert points[0] == Point2((0, 1))
        assert points[1] == Point2((-1, 0))
        assert points[2] == Point2((0, -1))
        assert points[3] == Point2((1, 0))
