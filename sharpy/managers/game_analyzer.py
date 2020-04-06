from typing import Tuple

from sharpy.managers import EnemyArmyPredicter
from sharpy.managers.game_states.advantage import at_least_clear_disadvantage, at_least_clear_advantage, \
    at_least_advantage, at_least_small_disadvantage, at_least_small_advantage
from sharpy.managers.income_calculator import GAS_MINE_RATE
from sharpy.general.extended_power import ExtendedPower
from sharpy.tools import IntervalFunc
from sharpy.unit_count import UnitCount
from sc2 import UnitTypeId, Result, List, Dict

from sharpy.managers.manager_base import ManagerBase
from sharpy.managers.game_states import *
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class GameAnalyzer(ManagerBase):
    def __init__(self):
        super().__init__()
        self._enemy_air_percentage = 0
        self._our_income_advantage = 0
        self._our_predicted_army_advantage = 0
        self._our_predicted_tech_advantage = 0
        self.enemy_gas_income = 0
        self.enemy_mineral_income = 0
        self.our_zones = 0
        self.enemy_zones = 0
        self.our_power: ExtendedPower = None
        self.enemy_power: ExtendedPower = None
        self.enemy_predict_power: ExtendedPower = None
        self.predicted_defeat_time = 0.0
        self.minerals_left: List[int] = []
        self.vespene_left: List[int] = []
        self.resource_updater: IntervalFunc = None

        self._last_income: Advantage = Advantage.Even
        self._last_army: Advantage = Advantage.Even
        self._last_predict: Advantage = Advantage.Even

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.enemy_predicter: EnemyArmyPredicter = knowledge.enemy_army_predicter
        self.our_power = ExtendedPower(self.unit_values)
        self.enemy_power: ExtendedPower = ExtendedPower(self.unit_values)
        self.enemy_predict_power: ExtendedPower = ExtendedPower(self.unit_values)
        self.resource_updater = IntervalFunc(self.ai, self.save_resources_status, 1)
        self.resource_updater.execute()

    def save_resources_status(self):
        self.minerals_left.append(self.ai.minerals)
        self.vespene_left.append(self.ai.vespene)

    async def update(self):
        self.resource_updater.execute()

        self.our_power.clear()
        self.our_zones = 0
        self.enemy_zones = 0
        our_income = self.knowledge.income_calculator.mineral_income + self.knowledge.income_calculator.gas_income

        if self.knowledge.my_worker_type is None:
            # random and we haven't seen enemy race yat
            enemy_workers = 12
        else:
            enemy_workers = self.knowledge.enemy_units_manager.enemy_worker_count
            if not self.knowledge.enemy_main_zone.is_scouted_at_least_once:
                enemy_workers += 12

        mineral_fields = 0
        for zone in self.knowledge.zone_manager.expansion_zones: # type: Zone
            if zone.is_enemys:
                self.enemy_zones += 1
                mineral_fields += len(zone.mineral_fields)
            if zone.is_ours:
                self.our_zones += 1

        built_vespene = len(self.cache.enemy(self.unit_values.gas_miners))
        self._enemy_gas_income = min(enemy_workers, built_vespene * 3) * GAS_MINE_RATE
        workers_on_minerals = min(mineral_fields * 2, enemy_workers - built_vespene * 3)
        workers_on_minerals = max(0, workers_on_minerals)
        self.enemy_mineral_income = workers_on_minerals

        enemy_income = self.enemy_mineral_income + self._enemy_gas_income
        self._our_income_advantage = our_income - enemy_income
        self.our_power.add_units(self.ai.units.filter(lambda u: u.is_ready
                                                                and u.type_id != self.knowledge.my_worker_type))

        self.enemy_predict_power = self.enemy_predicter.predicted_enemy_power
        self.enemy_power = self.enemy_predicter.enemy_power

        self._enemy_air_percentage = 0
        if self.enemy_predict_power.air_presence > 0:
            self._enemy_air_percentage = self.enemy_predict_power.air_power / self.enemy_predict_power.power

        being_defeated = self.predicting_defeat
        if being_defeated and self.predicted_defeat_time == 0.0:
            self.predicted_defeat_time = self.ai.time
        elif not being_defeated and self.predicted_defeat_time != 0.0:
            self.predicted_defeat_time = 0

        income = self._calc_our_income_advantage()
        army = self._calc_our_army_advantage()
        predict = self._calc_our_army_predict()

        if self._last_income != income:
            self.print(f'Income advantage is now {income.name}')

        if self._last_army  != army:
            self.print(f'Known army advantage is now {army.name}')

        if self._last_predict != predict:
            self.print(f'Predicted army advantage is now {predict.name}')

        self._last_income = income
        self._last_army = army
        self._last_predict = predict

    async def post_update(self):
        if self.debug:
            msg = f"Our income: {self.knowledge.income_calculator.mineral_income} / {round(self.knowledge.income_calculator.gas_income)}"
            msg += f"\nEnemy income: {self.enemy_mineral_income} / {round(self.enemy_gas_income)}"
            msg += f"\nResources: {round(self._our_income_advantage)}+{self.our_zones - self.enemy_zones}" \
                f" ({self.our_income_advantage.name})"
            msg += f"\nArmy: {round(self.our_power.power)} vs" \
                f" {round(self.enemy_power.power)} ({self.our_army_advantage.name})"
            msg += f"\nArmy predict: {round(self.our_power.power)} vs" \
                f" {round(self.enemy_predict_power.power)} ({self.our_army_predict.name})"
            msg += f"\nEnemy air: {self.enemy_air.name}"
            self.client.debug_text_2d(msg, Point2((0.4, 0.15)), None, 14)

    @property
    def our_income_advantage(self) -> Advantage:
        return self._last_income

    def _calc_our_income_advantage(self) -> Advantage:
        number = self._our_income_advantage + (self.our_zones - self.enemy_zones) * 10

        if number > 40:
            return Advantage.OverwhelmingAdvantage
        if number < -40:
            return Advantage.OverwhelmingDisadvantage

        if number > 20:
            return Advantage.ClearAdvantage
        if number < -20:
            return Advantage.ClearDisadvantage

        if number > 10:
            return Advantage.SmallAdvantage
        if number < -10:
            return Advantage.SmallDisadvantage

        if number > 5:
            return Advantage.SlightAdvantage
        if number < -5:
            return Advantage.SlightDisadvantage

        return Advantage.Even

    @property
    def army_at_least_clear_disadvantage(self) -> bool:
        return self.our_army_predict in at_least_clear_disadvantage

    @property
    def army_at_least_small_disadvantage(self) -> bool:
        return self.our_army_predict in at_least_small_disadvantage

    @property
    def army_at_least_clear_advantage(self) -> bool:
        return self.our_army_predict in at_least_clear_advantage

    @property
    def army_at_least_small_advantage(self) -> bool:
        return self.our_army_predict in at_least_small_advantage

    @property
    def army_at_least_advantage(self) -> bool:
        return self.our_army_predict in at_least_advantage

    @property
    def army_can_survive(self) -> bool:
        return self.our_army_predict not in at_least_small_disadvantage

    @property
    def predicting_victory(self) -> bool:
        return (self.our_army_predict == Advantage.OverwhelmingAdvantage
                and self.our_income_advantage == Advantage.OverwhelmingAdvantage)

    @property
    def been_predicting_defeat_for(self) -> float:
        if self.predicted_defeat_time == 0:
            return 0
        return self.ai.time - self.predicted_defeat_time

    @property
    def predicting_defeat(self) -> bool:
        return (self.our_army_predict == Advantage.OverwhelmingDisadvantage
                and (self.ai.supply_workers < 5 or self.our_income_advantage == Advantage.OverwhelmingDisadvantage))

    @property
    def our_army_predict(self) -> Advantage:
        return self._last_predict

    def _calc_our_army_predict(self) -> Advantage:
        if self.our_power.is_enough_for(self.enemy_predict_power, our_percentage=1 / 1.1):
            if self.our_power.power > 20 and self.our_power.is_enough_for(self.enemy_predict_power, our_percentage=1 / 3):
                return Advantage.OverwhelmingAdvantage
            if self.our_power.power > 10 and self.our_power.is_enough_for(self.enemy_predict_power, our_percentage=1 / 2):
                return Advantage.ClearAdvantage
            if self.our_power.power > 5 and self.our_power.is_enough_for(self.enemy_predict_power, our_percentage=1 / 1.4):
                return Advantage.SmallAdvantage
            return Advantage.SlightAdvantage

        if self.enemy_predict_power.is_enough_for(self.our_power, our_percentage=1 / 1.1):
            if self.enemy_predict_power.power > 20 and self.enemy_predict_power.is_enough_for(self.our_power, our_percentage=1 / 3):
                return Advantage.OverwhelmingDisadvantage
            if self.enemy_predict_power.power > 10 and self.enemy_predict_power.is_enough_for(self.our_power, our_percentage=1 / 2):
                return Advantage.ClearDisadvantage
            if self.enemy_predict_power.power > 5 and self.enemy_predict_power.is_enough_for(self.our_power, our_percentage=1 / 1.4):
                return Advantage.SmallDisadvantage
            return Advantage.SlightDisadvantage
        return Advantage.Even

    @property
    def our_army_advantage(self) -> Advantage:
        return self._last_army

    def _calc_our_army_advantage(self) -> Advantage:
        if self.our_power.is_enough_for(self.enemy_power, our_percentage=1 / 1.1):
            if self.our_power.power > 20 and self.our_power.is_enough_for(self.enemy_power, our_percentage=1 / 3):
                return Advantage.OverwhelmingAdvantage
            if self.our_power.power > 10 and self.our_power.is_enough_for(self.enemy_power, our_percentage=1 / 2):
                return Advantage.ClearAdvantage
            if self.our_power.power > 5 and self.our_power.is_enough_for(self.enemy_power, our_percentage=1 / 1.4):
                return Advantage.SmallAdvantage
            return Advantage.SlightAdvantage

        if self.enemy_power.is_enough_for(self.our_power, our_percentage=1 / 1.1):
            if self.enemy_power.power > 20 and self.enemy_power.is_enough_for(self.our_power, our_percentage=1 / 3):
                return Advantage.OverwhelmingDisadvantage
            if self.enemy_power.power > 10 and self.enemy_power.is_enough_for(self.our_power, our_percentage=1 / 2):
                return Advantage.ClearDisadvantage
            if self.enemy_power.power > 5 and self.enemy_power.is_enough_for(self.our_power, our_percentage=1 / 1.4):
                return Advantage.SmallDisadvantage
            return Advantage.SlightDisadvantage
        return Advantage.Even

    @property
    def enemy_air(self) -> AirArmy:
        if self._enemy_air_percentage > 0.90:
            return AirArmy.AllAir
        if self._enemy_air_percentage > 0.65:
            return AirArmy.AlmostAllAir
        if self._enemy_air_percentage > 0.35:
            return AirArmy.Mixed
        if self._enemy_air_percentage > 0:
            return AirArmy.SomeAir
        return AirArmy.NoAir

    async def on_end(self, game_result: Result):
        own_types: List[UnitTypeId] = []
        own_types_left: Dict[UnitTypeId, int] = {}
        enemy_types: List[UnitTypeId] = []
        enemy_types_left: Dict[UnitTypeId, int] = {}

        lost_data = self.knowledge.lost_units_manager.get_own_enemy_lost_units()
        own_lost: Dict[UnitTypeId, List[Unit]] = lost_data[0]
        enemy_lost: Dict[UnitTypeId, List[Unit]] = lost_data[1]

        for unit_type, units in self.cache.own_unit_cache.items():  # type: (UnitTypeId, Units)
            type_id = self.unit_values.real_type(unit_type)
            if type_id not in own_types:
                own_types.append(type_id)
            val = own_types_left.get(type_id, 0)
            own_types_left[type_id] = val + units.amount

        for unit_count in self.knowledge.enemy_units_manager.enemy_composition:  # type: UnitCount
            unit_type = unit_count.enemy_type
            if unit_type not in enemy_types:
                enemy_types.append(unit_type)
            val = enemy_types_left.get(unit_type, 0)
            enemy_types_left[unit_type] = val + unit_count.count

        for unit_type, units in own_lost.items():  # type: (UnitTypeId, List[Unit])
            if unit_type not in own_types:
                own_types.append(unit_type)

        for unit_type, units in enemy_lost.items():  # type: (UnitTypeId, List[Unit])
            if unit_type not in enemy_types:
                enemy_types.append(unit_type)

        self.print_end("Own units:")
        self._print_by_type(own_types, own_lost, own_types_left)
        self.print_end("Enemy units:")
        self._print_by_type(enemy_types, enemy_lost, enemy_types_left)

        maxed_minerals = max(self.minerals_left)
        avg_minerals = sum(self.minerals_left) / len(self.minerals_left)

        maxed_gas = max(self.vespene_left)
        avg_gas = sum(self.vespene_left) / len(self.vespene_left)
        self.print_end(f'Minerals max {maxed_minerals} Average {round(avg_minerals)}')
        self.print_end(f'Vespene max {maxed_gas} Average {round(avg_gas)}')

    def _print_by_type(self, types: List[UnitTypeId], lost_units: Dict[UnitTypeId, List[Unit]],
                       left_units: Dict[UnitTypeId, int]):

        def get_counts(unit_type: UnitTypeId) -> tuple:
            dead = len(lost_units.get(unit_type, []))
            alive = left_units.get(unit_type, 0)
            total = dead + alive
            return total, alive, dead

        # Sort types by total count
        types = sorted(types, key=lambda t: get_counts(t)[0], reverse=True)

        for unit_type in types:
            counts = get_counts(unit_type)
            self.print_end(f"{str(unit_type.name).ljust(17)} "
                           f"total: {str(counts[0]).rjust(3)} "
                           f"alive: {str(counts[1]).rjust(3)} "
                           f"dead: {str(counts[2]).rjust(3)} ")

    def print_end(self, msg: str):
        self.knowledge.print(msg, "GameAnalyzerEnd", stats=False)
