from sharpy.general.unit_value import is_townhall, UnitTypeId


class TestUnitValue:
    def test_is_townhall_returns_true_with_real_townhall_types(self):
        # Protoss
        assert is_townhall(UnitTypeId.NEXUS)
        # Terran
        assert is_townhall(UnitTypeId.COMMANDCENTER)
        assert is_townhall(UnitTypeId.ORBITALCOMMAND)
        assert is_townhall(UnitTypeId.PLANETARYFORTRESS)
        assert is_townhall(UnitTypeId.COMMANDCENTERFLYING)
        assert is_townhall(UnitTypeId.ORBITALCOMMANDFLYING)
        # Zerg
        assert is_townhall(UnitTypeId.HATCHERY)
        assert is_townhall(UnitTypeId.LAIR)
        assert is_townhall(UnitTypeId.HIVE)

    def test_is_townhall_returns_false_with_other_buildings(self):
        assert not is_townhall(UnitTypeId.SUPPLYDEPOT)
        assert not is_townhall(UnitTypeId.BARRACKS)
        assert not is_townhall(UnitTypeId.GATEWAY)
        assert not is_townhall(UnitTypeId.SPAWNINGPOOL)
