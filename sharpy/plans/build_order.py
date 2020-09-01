from typing import List, Union, Callable, Tuple

import sc2
from sc2 import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

from sharpy.plans.acts import Tech, ActUnit, ActBase, merge_to_act
from sharpy.plans.acts.grid_building import GridBuilding
from sharpy.plans.build_step import Step
from sharpy.plans.require import (
    UnitReady,
    SupplyLeft,
    TechReady,
    All,
    Any,
    EnemyUnitExists,
)
from sharpy.plans.sequential_list import SequentialList
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sharpy.knowledges import Knowledge


class BuildOrder(ActBase):
    def __init__(
        self,
        obj: Union[
            Union[ActBase, list, Callable[["Knowledge"], bool]],
            List[Union[ActBase, list, Callable[["Knowledge"], bool]]],
        ],
        *argv,
    ):
        """
        Build order is a list of actions that are executed sequentially, but they are not blocking.
        When every act in build order returns true, so will also build order.

        @param orders: build order can accept lists, acts and custom methods as parameters.
        @param argv: same type requirements as for orders, but you can skip [] syntax by using argv
        """
        super().__init__()

        self.orders: List[ActBase] = []
        if len(argv) > 0 or isinstance(obj, ActBase) or isinstance(obj, Callable):
            orders = [obj] + list(argv)
        else:
            orders = obj

        for order in orders:
            assert order is not None

            if isinstance(order, list):
                self.orders.append(SequentialList(order))
            else:
                self.orders.append(merge_to_act(order))

    async def debug_draw(self):
        for order in self.orders:
            await order.debug_draw()

    @property
    def glaives_upgrade(self) -> UpgradeId:
        return UpgradeId.ADEPTPIERCINGATTACK

    def RequireAnyEnemyUnits(self, unit_types: List[UnitTypeId], count: int) -> Any:
        require_list = []
        for unit_type in unit_types:
            require_list.append(EnemyUnitExists(unit_type, count))
        return Any(require_list)

    @property
    def pylons(self) -> List[Step]:
        return [
            Step(UnitReady(UnitTypeId.PYLON, 1), None),
            Step(SupplyLeft(4), GridBuilding(UnitTypeId.PYLON, 2)),
            Step(UnitReady(UnitTypeId.PYLON, 2), None),
            Step(SupplyLeft(8), GridBuilding(UnitTypeId.PYLON, 3)),
            Step(UnitReady(UnitTypeId.PYLON, 3), None),
            Step(SupplyLeft(10), GridBuilding(UnitTypeId.PYLON, 4)),
            Step(UnitReady(UnitTypeId.PYLON, 4), None),
            Step(SupplyLeft(15), GridBuilding(UnitTypeId.PYLON, 5)),
            Step(UnitReady(UnitTypeId.PYLON, 4), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 6)),
            Step(UnitReady(UnitTypeId.PYLON, 5), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 7)),
            Step(UnitReady(UnitTypeId.PYLON, 6), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 8)),
            Step(UnitReady(UnitTypeId.PYLON, 7), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 10)),
            Step(UnitReady(UnitTypeId.PYLON, 9), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 12)),
            Step(UnitReady(UnitTypeId.PYLON, 11), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 14)),
            Step(UnitReady(UnitTypeId.PYLON, 13), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.PYLON, 16)),
            Step(UnitReady(UnitTypeId.PYLON, 16), GridBuilding(UnitTypeId.PYLON, 18)),
            Step(UnitReady(UnitTypeId.PYLON, 18), GridBuilding(UnitTypeId.PYLON, 20)),
        ]

    @property
    def depots(self) -> List[Step]:
        return [
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 1), None),
            Step(SupplyLeft(6), GridBuilding(UnitTypeId.SUPPLYDEPOT, 2)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 2), None),
            Step(SupplyLeft(12), GridBuilding(UnitTypeId.SUPPLYDEPOT, 3)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 3), None),
            Step(SupplyLeft(14), GridBuilding(UnitTypeId.SUPPLYDEPOT, 4)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 4), None),
            Step(SupplyLeft(16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 5)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 4), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 6)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 5), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 7)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 6), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 8)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 7), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 10)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 9), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 12)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 11), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 14)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 13), None),
            Step(SupplyLeft(20), GridBuilding(UnitTypeId.SUPPLYDEPOT, 16)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 16), GridBuilding(UnitTypeId.SUPPLYDEPOT, 18)),
            Step(UnitReady(UnitTypeId.SUPPLYDEPOT, 18), GridBuilding(UnitTypeId.SUPPLYDEPOT, 20)),
        ]

    @property
    def overlords(self) -> List[Step]:
        return [
            Step(UnitReady(UnitTypeId.OVERLORD, 1), None),
            Step(SupplyLeft(4), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 2)),
            Step(UnitReady(UnitTypeId.OVERLORD, 2), None),
            Step(SupplyLeft(8), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 3)),
            Step(UnitReady(UnitTypeId.OVERLORD, 3), None),
            Step(SupplyLeft(10), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 4)),
            Step(UnitReady(UnitTypeId.OVERLORD, 4), None),
            Step(SupplyLeft(15), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 5)),
            Step(UnitReady(UnitTypeId.OVERLORD, 4), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 6)),
            Step(UnitReady(UnitTypeId.OVERLORD, 5), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 7)),
            Step(UnitReady(UnitTypeId.OVERLORD, 6), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 8)),
            Step(UnitReady(UnitTypeId.OVERLORD, 7), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 10)),
            Step(UnitReady(UnitTypeId.OVERLORD, 9), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 12)),
            Step(UnitReady(UnitTypeId.OVERLORD, 11), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 14)),
            Step(UnitReady(UnitTypeId.OVERLORD, 13), None),
            Step(SupplyLeft(20), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 16)),
            Step(UnitReady(UnitTypeId.OVERLORD, 16), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 18)),
            Step(UnitReady(UnitTypeId.OVERLORD, 18), ActUnit(UnitTypeId.OVERLORD, UnitTypeId.LARVA, 21)),
        ]

    @property
    def forge_upgrades_armor_first(self) -> List[Step]:
        return [
            # Armor
            Step(UnitReady(UnitTypeId.FORGE, 1), Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)]
                ),
            ),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL2, 1)]
                ),
            ),
            # Weapons
            Step(None, Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, 1)]
                ),
            ),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, 1)]
                ),
            ),
            # Shields
            Step(None, Tech(UpgradeId.PROTOSSSHIELDSLEVEL1)),
            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), None),
            Step(TechReady(UpgradeId.PROTOSSSHIELDSLEVEL1, 1), Tech(UpgradeId.PROTOSSSHIELDSLEVEL2)),
            Step(TechReady(UpgradeId.PROTOSSSHIELDSLEVEL2, 1), Tech(UpgradeId.PROTOSSSHIELDSLEVEL3)),
        ]

    @property
    def forge_upgrades_all(self) -> List[Step]:
        return [
            # Weapons
            Step(None, Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, 1)]
                ),
            ),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, 1)]
                ),
            ),
            # Armor
            Step(UnitReady(UnitTypeId.FORGE, 1), Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)]
                ),
            ),
            Step(
                None,
                Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
                skip_until=All(
                    [UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL2, 1)]
                ),
            ),
            # Shields
            Step(None, Tech(UpgradeId.PROTOSSSHIELDSLEVEL1)),
            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), None),
            Step(TechReady(UpgradeId.PROTOSSSHIELDSLEVEL1, 1), Tech(UpgradeId.PROTOSSSHIELDSLEVEL2)),
            Step(TechReady(UpgradeId.PROTOSSSHIELDSLEVEL2, 1), Tech(UpgradeId.PROTOSSSHIELDSLEVEL3)),
        ]

    @property
    def air_upgrades_all(self) -> List[Step]:
        return [
            Step(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)),
            Step(None, Tech(UpgradeId.PROTOSSAIRARMORSLEVEL1)),
            Step(UnitReady(UnitTypeId.FLEETBEACON, 1), None),
            Step(TechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL1), Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL2)),
            Step(TechReady(UpgradeId.PROTOSSAIRARMORSLEVEL1), Tech(UpgradeId.PROTOSSAIRARMORSLEVEL2)),
            Step(TechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL2), Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL3)),
            Step(TechReady(UpgradeId.PROTOSSAIRARMORSLEVEL2), Tech(UpgradeId.PROTOSSAIRARMORSLEVEL3)),
        ]

    @property
    def Infantry_upgrades_all(self) -> List[Step]:
        return [
            # Weapons
            Step(None, Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)),
            Step(
                None,
                Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2),
                skip_until=All([UnitReady(UnitTypeId.ARMORY, 1), TechReady(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1, 1)]),
            ),
            Step(
                None,
                Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3),
                skip_until=All([UnitReady(UnitTypeId.ARMORY, 1), TechReady(UpgradeId.TERRANINFANTRYARMORSLEVEL2, 1)]),
            ),
            # Armor
            Step(UnitReady(UnitTypeId.FORGE, 1), Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL1)),
            Step(
                None,
                Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL2),
                skip_until=All([UnitReady(UnitTypeId.ARMORY, 1), TechReady(UpgradeId.TERRANINFANTRYARMORSLEVEL1, 1)]),
            ),
            Step(
                None,
                Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL3),
                skip_until=All([UnitReady(UnitTypeId.ARMORY, 1), TechReady(UpgradeId.TERRANINFANTRYARMORSLEVEL2, 1)]),
            ),
        ]

    async def start(self, knowledge: "Knowledge"):
        await super().start(knowledge)
        for order in self.orders:
            await self.start_component(order, knowledge)

    async def execute(self) -> bool:
        result = True
        for order in self.orders:
            if not await order.execute():
                result = False

        return result
