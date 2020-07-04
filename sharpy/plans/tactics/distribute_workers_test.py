import math
import sys
from random import randint
from typing import Dict, Optional, Union

import numpy
import pytest
from unittest import mock

from sc2 import UnitTypeId, Race, BotAI, AbilityId
from sc2.constants import ALL_GAS, mineral_ids, IS_STRUCTURE, IS_MINE
from sc2.distances import DistanceCalculation
from sc2.ids.upgrade_id import UpgradeId
from sc2.pixel_map import PixelMap
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units

from .distribute_workers import DistributeWorkers
from ...general.zone import Zone
from ...knowledges import Knowledge, KnowledgeBot
from ...managers.roles import UnitTask
from ...managers.unit_value import BUILDING_IDS

MAIN_POINT = Point2((10, 10))
NATURAL_POINT = Point2((10, 60))
ENEMY_MAIN_POINT = Point2((90, 90))
ENEMY_NATURAL_POINT = Point2((90, 40))


def mock_ai() -> BotAI:
    ai = BotAI()
    ai.unit_command_uses_self_do = True
    ai._initialize_variables()
    # ai = mock.Mock(bot_object)
    ai._distances_override_functions(0)
    ai.actions = []
    ai.config = {"general": mock.Mock(), "debug_log": mock.Mock()}
    ai.config["general"].getboolean = lambda x: False
    ai.config["debug_log"].getboolean = lambda x, fallback: False
    ai.my_race = Race.Protoss
    ai.enemy_race = Race.Protoss

    ai.state = mock.Mock()
    ai.state.effects = []
    ai.state.visibility.__getitem__ = lambda s, x: 2

    ai._client = mock.Mock()

    ai._game_info = mock.Mock()
    ai._game_info.player_start_location = MAIN_POINT
    ai._game_info.start_locations = [ENEMY_MAIN_POINT]
    ai._game_info.placement_grid.height = 100
    ai._game_info.placement_grid.width = 100
    ai._game_info.map_center = Point2((50, 50))
    ai._game_info.map_name = "Mock"
    ai._game_info.terrain_height.__getitem__ = lambda s, x: 0
    ai._game_info.terrain_height.data_numpy = [0]
    ai._game_info.map_ramps = []

    ai._game_data = mock.Mock()
    ai._game_data.unit_types = {}
    ai._game_data.units = {
        UnitTypeId.MINERALFIELD.value: mock.Mock(),
        UnitTypeId.PROBE.value: mock.Mock(),
    }

    ai._game_data.units[UnitTypeId.MINERALFIELD.value].has_minerals = True
    ai._game_data.units[UnitTypeId.MINERALFIELD.value].attributes = {}
    ai._game_data.units[UnitTypeId.PROBE.value].attributes = {}
    ai._game_data.abilities = {AbilityId.HARVEST_GATHER.value: mock.Mock()}
    ai._game_data.abilities[AbilityId.HARVEST_GATHER.value].id = AbilityId.HARVEST_GATHER

    for typedata in BUILDING_IDS:
        ai._game_data.units[typedata.value] = mock.Mock()
        ai._game_data.units[typedata.value].attributes = {IS_STRUCTURE}

    ai._game_data.units[UnitTypeId.ASSIMILATOR.value].has_vespene = True
    ai._game_data.units[UnitTypeId.ASSIMILATORRICH.value].has_vespene = True

    mineral = create_mineral(ai, Point2((16, 10)))
    mineral2 = create_mineral(ai, Point2((16, 60)))

    ai._expansion_positions_list = [MAIN_POINT, NATURAL_POINT, ENEMY_MAIN_POINT, ENEMY_NATURAL_POINT]
    ai._resource_location_to_expansion_position_dict = {mineral.position: MAIN_POINT, mineral2.position: NATURAL_POINT}

    return ai


async def mock_knowledge(ai) -> Knowledge:
    knowledge = Knowledge()
    knowledge.pre_start(ai, None)
    knowledge.get_boolean_setting = lambda x: False
    knowledge.ai.state.game_loop = 1
    knowledge.ai.orders = []
    knowledge.action_handler = mock.Mock()
    knowledge.zone_manager.expansion_zones = [Zone(MAIN_POINT, True, knowledge), Zone(NATURAL_POINT, False, knowledge)]
    knowledge.iteration = 1

    knowledge.pathing_manager = mock.Mock()
    knowledge.pathing_manager.path_finder_terrain.find_path = lambda p1, p2: (
        [p1, p2],
        math.hypot(p1[0] - p2[0], p1[1] - p2[1]),
    )

    knowledge._all_own = ai.all_own_units

    await knowledge.roles.start(knowledge)
    await knowledge.unit_cache.start(knowledge)
    await knowledge.unit_cache.update()

    await knowledge.zone_manager.start(knowledge)
    await knowledge.zone_manager.update()
    return knowledge


def create_mineral(ai: BotAI, position: Point2) -> Unit:
    mineral = mock_unit(ai, UnitTypeId.MINERALFIELD, position)
    ai.mineral_field.append(mineral)
    ai.resources.append(mineral)
    return mineral


def mock_unit(ai, type_id: UnitTypeId, position: Point2) -> Unit:
    proto_mock = mock.Mock()
    proto_mock.tag = randint(0, sys.maxsize)
    proto_mock.unit_type = type_id.value
    proto_mock.pos.x = position.x
    proto_mock.pos.y = position.y
    proto_mock.orders = []
    proto_mock.buff_ids = []

    if type_id in mineral_ids:
        proto_mock.mineral_contents = 1000
    else:
        proto_mock.mineral_contents = 0

    if type_id in ALL_GAS:
        proto_mock.vespene_contents = 1000
        proto_mock.assigned_harvesters = 0
        proto_mock.ideal_harvesters = 3
    else:
        proto_mock.vespene_contents = 0
    unit = Unit(proto_mock, ai)

    if type_id in {UnitTypeId.NEXUS}:
        proto_mock.assigned_harvesters = 0
        proto_mock.ideal_harvesters = 16
        ai.townhalls.append(unit)

    if type_id in ALL_GAS:
        ai.gas_buildings.append(unit)

    if unit.is_structure:
        proto_mock.health = 400  # Whatever
        proto_mock.health_max = 400  # Whatever
        proto_mock.shield = 400
        proto_mock.shield_max = 400
        ai.structures.append(unit)
        proto_mock.build_progress = 1
        ai.all_own_units.append(unit)
        proto_mock.alliance = IS_MINE

    if type_id in {UnitTypeId.PROBE}:
        proto_mock.health = 20
        proto_mock.health_max = 20
        proto_mock.shield = 20
        proto_mock.shield_max = 20
        ai.units.append(unit)
        ai.workers.append(unit)
        ai.all_own_units.append(unit)
        proto_mock.alliance = IS_MINE

    ai.all_units.append(unit)

    return unit


def set_fake_order(unit: Unit, command: AbilityId, target: Optional[Union[int, Point2]]):
    fake = mock.Mock()
    fake.ability_id = command.value
    if isinstance(target, int):
        fake.target_unit_tag = target
        fake.HasField = lambda key: False
    else:
        fake.target_world_space_pos = target
        fake.HasField = lambda key: True

    fake.progress = 0

    unit._proto.orders = [fake]


class TestDistributeWorkers:
    @pytest.mark.asyncio
    async def test_assign_idle_to_nexus(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))

        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(0, worker1)
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == ai.mineral_field[0].tag

    @pytest.mark.asyncio
    async def test_assign_idle_to_gas(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 0
        nexus1._proto.ideal_harvesters = 0

        gas = mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        ai.units.append(worker1)
        ai.workers.append(worker1)
        ai.all_units.append(worker1)

        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(0, worker1)
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == gas.tag

    @pytest.mark.asyncio
    async def test_balance_assign_idle_to_gas(self):
        distribute_workers = DistributeWorkers(min_gas=1)
        distribute_workers.aggressive_gas_fill = True
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 0
        nexus1._proto.ideal_harvesters = 16

        gas = mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        ai.units.append(worker1)
        ai.workers.append(worker1)
        ai.all_units.append(worker1)

        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(0, worker1)
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == gas.tag

    @pytest.mark.asyncio
    async def test_balance_assign_idle_to_nexus(self):
        distribute_workers = DistributeWorkers(min_gas=0)
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 0
        nexus1._proto.ideal_harvesters = 16

        mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        ai.units.append(worker1)
        ai.workers.append(worker1)
        ai.all_units.append(worker1)

        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(0, worker1)
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == ai.mineral_field[0].tag

    @pytest.mark.asyncio
    async def test_balance_max_gas_assign_idle_to_nexus(self):
        distribute_workers = DistributeWorkers(min_gas=0, max_gas=0)
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 16
        nexus1._proto.ideal_harvesters = 16

        mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        ai.units.append(worker1)
        ai.workers.append(worker1)
        ai.all_units.append(worker1)

        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(0, worker1)
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == ai.mineral_field[0].tag

    @pytest.mark.asyncio
    async def test_evacuate_zone_nexus(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 1

        mock_unit(ai, UnitTypeId.NEXUS, Point2(NATURAL_POINT))

        for i in range(0, 17):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 60)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[1].tag)

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)

        knowledge = await mock_knowledge(ai)
        for worker in ai.workers:
            knowledge.roles.set_task(UnitTask.Gathering, worker)

        knowledge.expansion_zones[0].needs_evacuation = True
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) == 1
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == ai.mineral_field[1].tag

    @pytest.mark.asyncio
    async def test_force_evacuate_zone_nexus(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 1

        mock_unit(ai, UnitTypeId.NEXUS, Point2(NATURAL_POINT))

        worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
        set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)
        knowledge = await mock_knowledge(ai)
        knowledge.roles.set_task(UnitTask.Gathering, worker1)
        knowledge.expansion_zones[0].needs_evacuation = True
        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].unit.tag == worker1.tag
        assert ai.actions[0].target.tag == ai.mineral_field[1].tag

    @pytest.mark.asyncio
    async def test_assign_surplus_to_gas(self):
        distribute_workers = DistributeWorkers(aggressive_gas_fill=True)
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 17

        gas = mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        for i in range(0, 17):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)

        knowledge = await mock_knowledge(ai)

        for worker in ai.workers:
            knowledge.roles.set_task(UnitTask.Gathering, worker)

        await distribute_workers.start(knowledge)
        await distribute_workers.execute()

        assert len(ai.actions) == 1
        assert ai.actions[0].target.tag == gas.tag

    @pytest.mark.asyncio
    async def test_assign_surplus_to_nexus(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 17

        nexus2 = mock_unit(ai, UnitTypeId.NEXUS, Point2(NATURAL_POINT))
        nexus2._proto.assigned_harvesters = 14

        for i in range(0, 17):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)

        for i in range(0, 14):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 60)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[1].tag)

        knowledge = await mock_knowledge(ai)

        for worker in ai.workers:
            knowledge.roles.set_task(UnitTask.Gathering, worker)

        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) > 0
        assert ai.actions[0].target.tag == ai.mineral_field[1].tag

    @pytest.mark.asyncio
    async def test_force_assign_to_gas(self):
        distribute_workers = DistributeWorkers(aggressive_gas_fill=True)
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 14

        gas = mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        for i in range(0, 14):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)

        knowledge = await mock_knowledge(ai)

        for worker in ai.workers:
            knowledge.roles.set_task(UnitTask.Gathering, worker)

        await distribute_workers.start(knowledge)
        await distribute_workers.execute()

        assert len(ai.actions) == 1
        assert ai.actions[0].target.tag == gas.tag

    @pytest.mark.asyncio
    async def test_no_force_assign_to_gas(self):
        distribute_workers = DistributeWorkers(aggressive_gas_fill=False)
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 14

        mock_unit(ai, UnitTypeId.ASSIMILATOR, Point2(MAIN_POINT))

        for i in range(0, 14):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)

        knowledge = await mock_knowledge(ai)

        for worker in ai.workers:
            knowledge.roles.set_task(UnitTask.Gathering, worker)

        await distribute_workers.start(knowledge)
        await distribute_workers.execute()

        assert len(ai.actions) == 0

    @pytest.mark.asyncio
    async def test_do_not_send_excess_workers(self):
        distribute_workers = DistributeWorkers()
        ai = mock_ai()

        nexus1 = mock_unit(ai, UnitTypeId.NEXUS, Point2(MAIN_POINT))
        nexus1._proto.assigned_harvesters = 17

        nexus2 = mock_unit(ai, UnitTypeId.NEXUS, Point2(NATURAL_POINT))
        nexus2._proto.assigned_harvesters = 16

        for i in range(0, 17):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 10)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[0].tag)

        for i in range(0, 16):
            worker1 = mock_unit(ai, UnitTypeId.PROBE, Point2((20, 60)))
            set_fake_order(worker1, AbilityId.HARVEST_GATHER, ai.mineral_field[1].tag)

        knowledge = await mock_knowledge(ai)

        for worker in ai.workers:
            knowledge.roles.set_task(UnitTask.Gathering, worker)

        await distribute_workers.start(knowledge)
        await distribute_workers.execute()
        assert len(ai.actions) == 0
