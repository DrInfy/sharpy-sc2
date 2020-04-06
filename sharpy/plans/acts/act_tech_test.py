from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from .act_tech import ActTech


class TestActTech:
    def test_SPIRE_and_GREATERSPIRE_found_implicitly_for_ZERGFLYERWEAPONSLEVEL2(self):
        act_tech = ActTech(UpgradeId.ZERGFLYERWEAPONSLEVEL2)

        assert UnitTypeId.SPIRE in act_tech.from_buildings
        assert UnitTypeId.GREATERSPIRE in act_tech.from_buildings
        assert 2 == len(act_tech.from_buildings)

    def test_ROACHWARREN_found_implicitly_for_GLIALRECONSTITUTION(self):
        act_tech = ActTech(UpgradeId.GLIALRECONSTITUTION)

        assert UnitTypeId.ROACHWARREN in act_tech.from_buildings
        assert 1 == len(act_tech.from_buildings)
