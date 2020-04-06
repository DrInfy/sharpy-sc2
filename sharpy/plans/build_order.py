from typing import List, Union

import sc2
from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from sharpy.plans.acts import ActTech, ActUnit, ActBase
from sharpy.plans.acts.grid_building import GridBuilding
from sharpy.plans.build_step import Step
from sharpy.plans.require import RequiredUnitReady, RequiredSupplyLeft, RequiredTechReady, RequiredAll, RequiredAny, \
    RequiredEnemyUnitExists
from sharpy.plans.sequential_list import SequentialList


class BuildOrder(ActBase):
    def __init__(self, orders: List[Union[ActBase, List[ActBase]]]):
        super().__init__()
        self.orders: List[Union[ActBase, List[ActBase]]] = orders
        self.orders: List[ActBase] = []
        for order in orders:
            if isinstance(order, ActBase):
                self.orders.append(order)
            elif isinstance(order, list):
                self.orders.append(SequentialList(order))
            else:
                assert False  # Invalid type

    async def debug_draw(self):
        for order in self.orders:
            await order.debug_draw()

    @property
    def glaives_upgrade(self) -> UpgradeId:
        return UpgradeId.ADEPTPIERCINGATTACK


    def RequireAnyEnemyUnits(self, unit_types: List[UnitTypeId], count: int) -> RequiredAny:
        require_list = []
        for unit_type in unit_types:
            require_list.append(RequiredEnemyUnitExists(unit_type, count))
        return RequiredAny(require_list)

    @property
    def pylons(self) -> List[Step]:
        return [
            Step(RequiredUnitReady(UnitTypeId.PYLON, 1), None),
            Step(RequiredSupplyLeft(4), GridBuilding(UnitTypeId.PYLON, 2)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 2), None),
            Step(RequiredSupplyLeft(8), GridBuilding(UnitTypeId.PYLON, 3)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 3), None),
            Step(RequiredSupplyLeft(10), GridBuilding(UnitTypeId.PYLON, 4)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 4), None),
            Step(RequiredSupplyLeft(15), GridBuilding(UnitTypeId.PYLON, 5)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 4), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 6)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 5), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 7)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 6), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 8)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 7), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 10)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 9), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 12)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 11), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 14)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 13), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 16)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 16), GridBuilding(UnitTypeId.PYLON, 18)),
            Step(RequiredUnitReady(UnitTypeId.PYLON, 18), GridBuilding(UnitTypeId.PYLON, 20)),
        ]

    @property
    def depots(self) -> List[Step]:
        return [
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 1), None),
            Step(RequiredSupplyLeft(6), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 2), None),
            Step(RequiredSupplyLeft(12), GridBuilding(UnitTypeId.SUPPLYDEPOT, 3)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 3), None),
            Step(RequiredSupplyLeft(14), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 4), None),
            Step(RequiredSupplyLeft(16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 5)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 4), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 6)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 5), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 7)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 6), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 8)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 7), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 10)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 9), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 12)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 11), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 14)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 13), None),
            Step(RequiredSupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 16)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 18)),
            Step(RequiredUnitReady(UnitTypeId.SUPPLYDEPOT, 18), GridBuilding(UnitTypeId.SUPPLYDEPOT, 20)),
        ]

    @property
    def overlords(self) -> List[Step]:
        return [
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 1), None),
            Step(RequiredSupplyLeft(4), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 2), None),
            Step(RequiredSupplyLeft(8), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 3)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 3), None),
            Step(RequiredSupplyLeft(10), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 4)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 4), None),
            Step(RequiredSupplyLeft(15), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 5)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 4), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 6)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 5), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 7)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 6), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 8)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 7), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 10)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 9), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 12)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 11), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 14)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 13), None),
            Step(RequiredSupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 16)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 16), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 18)),
            Step(RequiredUnitReady(UnitTypeId.OVERLORD, 18), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 21)),
        ]

    @property
    def forge_upgrades_armor_first(self) -> List[Step]:
        return [
            # Armor
            Step(RequiredUnitReady(UnitTypeId.FORGE, 1),
                 ActTech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                 skip_until=RequiredAll([
                          RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                          RequiredTechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)
                      ])),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL2, 1)
                       ])),
            # Weapons
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, 1)
                       ])),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, 1)]
                      )),
            # Shields
            Step(None,
                 ActTech(UpgradeId.PROTOSSSHIELDSLEVEL1)),

            Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), None),

            Step(RequiredTechReady(UpgradeId.PROTOSSSHIELDSLEVEL1, 1),
                 ActTech(UpgradeId.PROTOSSSHIELDSLEVEL2)),
            Step(RequiredTechReady(UpgradeId.PROTOSSSHIELDSLEVEL2, 1),
                 ActTech(UpgradeId.PROTOSSSHIELDSLEVEL3)),
        ]

    @property
    def forge_upgrades_all(self) -> List[Step]:
        return [
            # Weapons
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, 1)
                       ])),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, 1)
                       ])),
            
            # Armor
            Step(RequiredUnitReady(UnitTypeId.FORGE, 1),
                 ActTech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)
                       ])),
            Step(None,
                 ActTech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
                 skip_until=RequiredAll(
                          [RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
                           RequiredTechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL2, 1)
                       ])),
            # Shields
            Step(None,
                 ActTech(UpgradeId.PROTOSSSHIELDSLEVEL1)),

            Step(RequiredUnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), None),

            Step(RequiredTechReady(UpgradeId.PROTOSSSHIELDSLEVEL1, 1),
                 ActTech(UpgradeId.PROTOSSSHIELDSLEVEL2)),
            Step(RequiredTechReady(UpgradeId.PROTOSSSHIELDSLEVEL2, 1),
                 ActTech(UpgradeId.PROTOSSSHIELDSLEVEL3)),
        ]

    @property
    def air_upgrades_all(self) -> List[Step]:
        return [
            Step(RequiredUnitReady(UnitTypeId.CYBERNETICSCORE, 1),
                 ActTech(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)),
            Step(None,
                 ActTech(UpgradeId.PROTOSSAIRARMORSLEVEL1)),
            Step(RequiredUnitReady(UnitTypeId.FLEETBEACON, 1), None),
            Step(RequiredTechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL1),
                 ActTech(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)),
            Step(RequiredTechReady(UpgradeId.PROTOSSAIRARMORSLEVEL1),
                 ActTech(UpgradeId.PROTOSSAIRARMORSLEVEL2)),
            Step(RequiredTechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL2),
                 ActTech(UpgradeId.PROTOSSAIRWEAPONSLEVEL3)),
            Step(RequiredTechReady(UpgradeId.PROTOSSAIRARMORSLEVEL2),
                 ActTech(UpgradeId.PROTOSSAIRARMORSLEVEL3)),
        ]

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        for order in self.orders:
            await order.start(knowledge)


    async def execute(self) -> bool:
        result = True
        for order in self.orders:
            if not await order.execute():
                result = False

        return result
