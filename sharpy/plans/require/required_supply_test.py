import pytest

from unittest import mock

from .required_supply import RequiredSupply


class TestRequiredSupply:
    @pytest.mark.asyncio
    async def test_check_returns_false_when_supply_is_not_met(self):
        # Arrange
        req_supply = RequiredSupply(15)

        knowledge_mock = mock.Mock()
        knowledge_mock.ai.supply_used = 13
        await req_supply.start(knowledge_mock)

        # Act & Assert
        assert not req_supply.check()

    @pytest.mark.asyncio
    async def test_check_returns_true_when_supply_is_equal_to_requirement(self):
        # Arrange
        req_supply = RequiredSupply(15)

        knowledge_mock = mock.Mock()
        knowledge_mock.ai.supply_used = 15
        await req_supply.start(knowledge_mock)

        # Act & Assert
        assert req_supply.check()
