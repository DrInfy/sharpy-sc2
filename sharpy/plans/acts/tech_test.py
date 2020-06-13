import pytest
from unittest import mock

from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from .tech import Tech


def mock_knowledge() -> mock.Mock:
    knowledge_mock = mock.Mock()
    knowledge_mock.get_boolean_setting = lambda x: False
    knowledge_mock.ai._client = mock.Mock()
    knowledge_mock.version_manager.moved_upgrades = {}
    knowledge_mock.version_manager.disabled_upgrades = {UpgradeId.LURKERRANGE}
    return knowledge_mock


class TestActTech:
    @pytest.mark.asyncio
    async def test_SPIRE_and_GREATERSPIRE_found_implicitly_for_ZERGFLYERWEAPONSLEVEL2(self):
        act_tech = Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL2)
        await act_tech.start(mock_knowledge())

        assert UnitTypeId.SPIRE in act_tech.from_buildings
        assert UnitTypeId.GREATERSPIRE in act_tech.from_buildings
        assert 2 == len(act_tech.from_buildings)

    @pytest.mark.asyncio
    async def test_ROACHWARREN_found_implicitly_for_GLIALRECONSTITUTION(self):
        act_tech = Tech(UpgradeId.GLIALRECONSTITUTION)
        await act_tech.start(mock_knowledge())

        assert UnitTypeId.ROACHWARREN in act_tech.from_buildings
        assert 1 == len(act_tech.from_buildings)

    @pytest.mark.asyncio
    async def test_LURKERRANGE_disabled_in_VersionManager(self):
        act_tech = Tech(UpgradeId.LURKERRANGE)
        await act_tech.start(mock_knowledge())

        assert not act_tech.enabled

    @pytest.mark.asyncio
    async def test_TERRANVEHICLEANDSHIPARMORSLEVEL3_enabled_in_VersionManager(self):
        act_tech = Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3)
        await act_tech.start(mock_knowledge())

        assert act_tech.enabled
