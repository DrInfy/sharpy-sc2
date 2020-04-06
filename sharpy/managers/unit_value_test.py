from sc2 import UnitTypeId

from .unit_value import UnitValue


class TestUnitValue:
    def test_is_townhall_returns_true_with_real_townhall_types(self):
        unit_value = UnitValue()

        # Protoss
        assert unit_value.is_townhall(UnitTypeId.NEXUS)
        # Terran
        assert unit_value.is_townhall(UnitTypeId.COMMANDCENTER)
        assert unit_value.is_townhall(UnitTypeId.ORBITALCOMMAND)
        assert unit_value.is_townhall(UnitTypeId.PLANETARYFORTRESS)
        assert unit_value.is_townhall(UnitTypeId.COMMANDCENTERFLYING)
        assert unit_value.is_townhall(UnitTypeId.ORBITALCOMMANDFLYING)
        # Zerg
        assert unit_value.is_townhall(UnitTypeId.HATCHERY)
        assert unit_value.is_townhall(UnitTypeId.LAIR)
        assert unit_value.is_townhall(UnitTypeId.HIVE)

    def test_is_townhall_returns_false_with_other_buildings(self):
        unit_value = UnitValue()

        assert not unit_value.is_townhall(UnitTypeId.SUPPLYDEPOT)
        assert not unit_value.is_townhall(UnitTypeId.BARRACKS)
        assert not unit_value.is_townhall(UnitTypeId.GATEWAY)
        assert not unit_value.is_townhall(UnitTypeId.SPAWNINGPOOL)
