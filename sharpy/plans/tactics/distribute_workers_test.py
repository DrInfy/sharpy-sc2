from typing import Dict

import pytest
from unittest import mock

from sc2 import UnitTypeId, Race, BotAI
from sc2.constants import ALL_GAS
from sc2.distances import DistanceCalculation
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from .distribute_workers import DistributeWorkers
from ...general.zone import Zone
from ...knowledges import Knowledge, KnowledgeBot

MAIN_POINT = Point2((10, 10))
NATURAL_POINT = Point2((10, 60))


def mock_ai() -> KnowledgeBot:
    ai = mock.Mock()
    ai.actions = []
    ai.config = {"general": mock.Mock(), "debug_log": mock.Mock()}
    ai.config["general"].getboolean = lambda x: False
    ai.config["debug_log"].getboolean = lambda x, fallback: False
    ai.game_info.map_name = "Mock"
    ai.enemy_structures = Units([], ai)
    ai.enemy_units = Units([], ai)
    ai.all_enemy_units = Units([], ai)
    ai.all_units = Units([], ai)
    ai.gas_buildings = Units([], ai)
    ai.townhalls = Units([], ai)
    ai.units = Units([], ai)
    ai.workers = Units([], ai)
    ai.mineral_field = Units([], ai)
    ai.my_race = Race.Protoss
    ai.enemy_race = Race.Protoss
    ai.state.effects = []
    ai._distance_squared_unit_to_unit = BotAI._distance_squared_unit_to_unit_method0
    ai.calculate_distances = BotAI._calculate_distances_method1
    ai._distance_units_to_pos = BotAI._distance_units_to_pos

    ai._game_info.placement_grid.height = 100
    ai._game_info.placement_grid.width = 100
    ai._game_data.unit_types = {}

    mineral = mock_unit(ai, UnitTypeId.MINERALFIELD, Point2((22, 10)))
    ai.mineral_field.append(mineral)
    mineral2 = mock_unit(ai, UnitTypeId.MINERALFIELD, Point2((22, 60)))
    ai.mineral_field.append(mineral2)

    ai.expansion_locations_dict = {MAIN_POINT: Units([mineral], ai), NATURAL_POINT: Units([mineral2], ai)}

    return ai


async def mock_knowledge(ai) -> Knowledge:
    knowledge = Knowledge()
    knowledge.pre_start(ai, None)
    knowledge.get_boolean_setting = lambda x: False
    knowledge.ai.state.game_loop = 1
    knowledge.ai.orders = []
    knowledge.action_handler = mock.Mock()
    knowledge.zone_manager.expansion_zones = [Zone(MAIN_POINT, True, knowledge), Zone(NATURAL_POINT, False, knowledge)]
    await knowledge.roles.start(knowledge)
    await knowledge.unit_cache.start(knowledge)
    await knowledge.unit_cache.update()
    await knowledge.zone_manager.update()
    return knowledge


def mock_unit(ai, type_id: UnitTypeId, position: Point2) -> Unit:
    proto_mock = mock.Mock()
    proto_mock.unit_type = type_id.value
    proto_mock.pos.x = position.x
    proto_mock.pos.y = position.y
    proto_mock.orders = []
    proto_mock.buff_ids = []
    if type_id in ALL_GAS:
        proto_mock.vespene_contents = 1000
    else:
        proto_mock.vespene_contents = 0
    unit = Unit(proto_mock, ai)

    return unit


class TestDistributeWorkers:
    @pytest.mark.asyncio
    async def test_assign_idle_to_nexus(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 0
        nexus1._proto.ideal_harvesters = 16
        ai.townhalls.append(nexus1)
        ai.all_units.append(nexus1)

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        ai.units.append(worker1)
        ai.workers.append(worker1)
        ai.all_units.append(worker1)

        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(0, worker1)
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(knowledge.ai.actions) > 0

    @pytest.mark.asyncio
    async def test_assign_idle_to_gas(self):
        assert False

    @pytest.mark.asyncio
    async def test_evacuate_zone_nexus(self):
        assert False

    @pytest.mark.asyncio
    async def test_assign_surplus_to_gas(self):
        assert False

    @pytest.mark.asyncio
    async def test_assign_surplus_to_nexus(self):
        assert False

    @pytest.mark.asyncio
    async def test_force_assign_to_gas(self):
        assert False
