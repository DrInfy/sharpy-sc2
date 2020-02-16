from typing import List, Union

from sharpy.general.zone import Zone
from sharpy.plans import BuildOrder, SequentialList, StepBuildGas, Step
from sharpy.plans.acts import ActBase, ActBuilding, DefensiveBuilding, DefensePosition
from sc2 import UnitTypeId, AbilityId, Race
from sc2.ids.buff_id import BuffId
from sc2.unit import Unit
from sharpy.plans.acts.zerg import MorphLair, ZergUnit, AutoOverLord
from sharpy.plans.require import RequiredSupply
from sharpy.plans.tactics import PlanDistributeWorkers


class CounterTerranTie(BuildOrder):
    def __init__(self, orders: List[Union[ActBase, List[ActBase]]]):
        """
        Build order package that replaces normal build order for Zerg with one that builds mutalisks to destroy terran
        flying buildings.
        Add any PlanDistributeWorkers acts with orders
        """
        cover_list = SequentialList([
            PlanDistributeWorkers(),
            AutoOverLord(),
            Step(None, ZergUnit(UnitTypeId.DRONE, 20), skip=RequiredSupply(198)),
            StepBuildGas(4, None),
            MorphLair(),
            ActBuilding(UnitTypeId.SPIRE, 1),
            Step(None, DefensiveBuilding(UnitTypeId.SPORECRAWLER, DefensePosition.BehindMineralLineCenter),
                 skip_until=RequiredSupply(199)),
            Step(None, DefensiveBuilding(UnitTypeId.SPINECRAWLER, DefensePosition.Entrance),
                 skip_until=RequiredSupply(199)),
            ZergUnit(UnitTypeId.MUTALISK, 10),
        ])

        new_build_order = [
            Step(None, cover_list, skip_until=self.should_build_mutalisks),
            Step(None, BuildOrder(orders), skip=self.should_build_mutalisks)
        ]
        super().__init__(new_build_order)

    def should_build_mutalisks(self, knowledge):
        if self.knowledge.enemy_race != Race.Terran:
            return False

        if len(self.cache.own({UnitTypeId.MUTALISK, UnitTypeId.CORRUPTOR})) >= 10:
            return False

        if len(self.ai.enemy_units.not_flying) > 1:
            return False

        if self.ai.supply_workers < 20 and self.ai.supply_used < 190:
            return False

        if self.ai.supply_used < 70:
            return False

        main_zone: Zone = self.knowledge.enemy_main_zone
        if not main_zone.is_scouted_at_least_once:
            return False

        buildings = self.ai.enemy_structures
        return len(buildings) == len(buildings.flying)
