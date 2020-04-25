import pytest
from unittest import mock

from sharpy.knowledges import Knowledge
from sharpy.managers import DataManager, ManagerBase


class TestDataManager(DataManager):
    def should_be_true(self) -> bool:
        return self.debug is False


class CustomTestManager(ManagerBase):
    @property
    def test_property(self) -> int:
        return 1

    async def update(self):
        pass

    async def post_update(self):
        pass


class TestKnowledge:
    @pytest.mark.asyncio
    async def test_get_DataManager(self):
        knowledge = Knowledge()
        knowledge._set_managers(None)

        data_manager = knowledge.get_manager(DataManager)

        assert data_manager is not None
        assert isinstance(data_manager, DataManager)

    @pytest.mark.asyncio
    async def test_get_DataManager_from_override(self):
        knowledge = Knowledge()
        knowledge.data_manager = TestDataManager()
        knowledge._set_managers(None)

        data_manager = knowledge.get_manager(DataManager)

        assert data_manager is not None
        assert isinstance(data_manager, TestDataManager)
        assert isinstance(data_manager, DataManager)

    @pytest.mark.asyncio
    async def test_get_TestDataManager_from_override(self):
        knowledge = Knowledge()
        knowledge.data_manager = TestDataManager()
        knowledge._set_managers(None)

        data_manager = knowledge.get_manager(TestDataManager)

        assert data_manager is not None
        assert isinstance(data_manager, TestDataManager)
        assert isinstance(data_manager, DataManager)
        assert data_manager.should_be_true()

    @pytest.mark.asyncio
    async def test_get_CustomManager_from_override(self):
        knowledge = Knowledge()
        knowledge._set_managers([CustomTestManager()])

        custom_manager = knowledge.get_manager(CustomTestManager)

        assert custom_manager is not None
        assert isinstance(custom_manager, CustomTestManager)
        assert isinstance(custom_manager, ManagerBase)
        assert custom_manager.test_property == 1

    @pytest.mark.asyncio
    async def test_get_None_CustomManager_not_set(self):
        knowledge = Knowledge()
        knowledge._set_managers(None)

        custom_manager = knowledge.get_manager(CustomTestManager)

        assert custom_manager is None
