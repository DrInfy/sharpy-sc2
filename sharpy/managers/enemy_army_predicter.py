from typing import Dict, Optional, List

from sharpy.managers.manager_base import ManagerBase
from sharpy.managers.enemy_units_manager import EnemyUnitsManager
from sharpy.general.extended_power import ExtendedPower
from sharpy.managers.predict.composition_guesser import CompositionGuesser
from sharpy.unit_count import UnitCount
from sharpy.managers.lostunitsmanager import LostUnitsManager

from sharpy.tools.interval_func import IntervalFuncAsync
from sc2 import UnitTypeId, Race
from sc2.client import Client
from sc2.position import Point2
from sc2.unit import Unit

INTERVAL = 5
MINERAL_MINING_SPEED = 1800.0 / 15 / 60 / 2


class EnemyArmyPredicter(ManagerBase):
    def __init__(self):
        super().__init__()

    async def start(self, knowledge: 'Knowledge'):
        await super().start(knowledge)
        self.enemy_units_manager: EnemyUnitsManager = self.knowledge.enemy_units_manager

        self.lost_units_manager: LostUnitsManager = knowledge.lost_units_manager
        self.unit_values: 'UnitValue' = knowledge.unit_values

        self.updater = IntervalFuncAsync(self.ai, self._real_update, INTERVAL)

        self.enemy_base_value_minerals = 400 + 12 * 50 + 50
        self.enemy_known_worker_count = 12

        self.mineral_dict: Dict['Zone', int] = {}

        # Last time minerals were updated
        self.mineral_updated_dict: Dict['Zone', float] = {}
        self.gas_dict: Dict[Point2, int] = {}

        for zone in knowledge.expansion_zones:
            minerals = 0
            if zone.last_minerals is not None:
                minerals = zone.last_minerals

            self.mineral_dict[zone] = minerals

        for geyser in self.ai.vespene_geyser: # type: Unit
            self.gas_dict[geyser.position] = 2250

        self.enemy_mined_minerals = 0
        self.enemy_mined_minerals_prediction = 0
        self.enemy_mined_gas = 0

        self.enemy_army_known_minerals = 0
        self.enemy_army_known_gas = 0

        self.own_army_value_minerals = 0
        self.own_army_value_gas = 0

        self.predicted_enemy_free_minerals = 0
        self.predicted_enemy_free_gas = 0

        self.predicted_enemy_army_minerals = 0
        self.predicted_enemy_army_gas = 0

        self.predicted_enemy_composition: List[UnitCount] = []

        self.enemy_power = ExtendedPower(self.unit_values)
        self.predicted_enemy_power = ExtendedPower(self.unit_values)

    @property
    def own_value(self):
        """ Our exact army value that we know of """
        return self.own_army_value_minerals + self.own_army_value_gas

    @property
    def enemy_value(self):
        """ Best estimation on how big value enemy army has """
        return self.predicted_enemy_army_minerals + self.predicted_enemy_army_gas

    async def update(self):
        await self.updater.execute()

    async def _real_update(self):
        await self.update_own_army_value()

        self.enemy_power.clear()
        self.predicted_enemy_power.clear()

        self.predicted_enemy_composition.clear()
        gas_miners = self.knowledge.known_enemy_structures.of_type(
            [UnitTypeId.ASSIMILATOR, UnitTypeId.EXTRACTOR, UnitTypeId.REFINERY])

        minerals_used: int = 0
        gas_used: int = 0
        enemy_composition = self.enemy_units_manager.enemy_composition
        self.enemy_known_worker_count = 0

        self.enemy_army_known_minerals = 0
        self.enemy_army_known_gas = 0

        self.predicted_enemy_free_minerals = 0
        self.predicted_enemy_free_gas = 0

        self.predicted_enemy_army_minerals = 0
        self.predicted_enemy_army_gas = 0

        for unit_count in enemy_composition:
            if unit_count.count > 0:
                # TODO: Overlords!
                if self.unit_values.is_worker(unit_count.enemy_type):
                    self.enemy_known_worker_count += unit_count.count

                mineral_value = self.unit_values.minerals(unit_count.enemy_type) * unit_count.count
                gas_value = self.unit_values.gas(unit_count.enemy_type) * unit_count.count
                minerals_used += mineral_value
                gas_used += gas_value

                if not self.unit_values.is_worker(unit_count.enemy_type) \
                        and self.unit_values.power_by_type(unit_count.enemy_type) > 0.25:
                    self.enemy_power.add_unit(unit_count.enemy_type, unit_count.count)

                    self.predicted_enemy_composition.append(unit_count)
                    # Save values as to what we know to be true
                    self.enemy_army_known_minerals += mineral_value
                    self.enemy_army_known_gas += gas_value

        mined_minerals: int = 0
        mined_minerals_predict: float = 0
        worker_count_per_base = 12  # TODO: Just random guess

        for zone in self.knowledge.enemy_expansion_zones:
            current_minerals = zone.last_minerals
            if current_minerals is None:
                current_minerals = 0

            last_minerals = self.mineral_dict.get(zone, 0)

            if last_minerals > current_minerals:
                self.mineral_dict[zone] = current_minerals
                self.mineral_updated_dict[zone] = self.ai.time

                if zone.is_enemys:
                    mined_minerals += last_minerals - current_minerals
            elif zone.is_enemys:
                prediction = last_minerals - (self.ai.time - self.mineral_updated_dict.get(zone, 0)) * MINERAL_MINING_SPEED * worker_count_per_base
                prediction = max(0.0, prediction)
                mined_minerals_predict += last_minerals - prediction

        self.enemy_mined_minerals += mined_minerals
        self.enemy_mined_minerals_prediction = round(self.enemy_mined_minerals + mined_minerals_predict)

        if gas_miners.exists:

            for miner in gas_miners:  # type: Unit
                last_gas = self.gas_dict.get(miner.position, 2250)
                if miner.is_visible:
                    gas = miner.vespene_contents
                else:
                    gas = max(0.0, last_gas - 169.61 / 60 * INTERVAL)

                self.gas_dict[miner.position] = gas
                self.enemy_mined_gas += last_gas - gas

        lost_tuple: tuple = self.lost_units_manager.calculate_enemy_lost_resources()
        minerals_used += lost_tuple[0]
        gas_used += lost_tuple[1]

        self.predicted_enemy_free_minerals = round(self.enemy_base_value_minerals
                                                   + self.enemy_mined_minerals_prediction
                                                   - minerals_used)

        self.predicted_enemy_free_gas = round(self.enemy_mined_gas - gas_used)

        if self.predicted_enemy_free_minerals < 0:
            # Possibly hidden base or more workers than we think?
            self.print(f"Predicting negative free minerals for enemy: {self.predicted_enemy_free_minerals}")

        await self.predict_enemy_composition()

        for unit_count in self.predicted_enemy_composition:
            self.predicted_enemy_power.add_unit(unit_count.enemy_type, unit_count.count)
            mineral_value = self.unit_values.minerals(unit_count.enemy_type) * unit_count.count
            gas_value = self.unit_values.minerals(unit_count.enemy_type) * unit_count.count
            self.predicted_enemy_army_minerals += mineral_value
            self.predicted_enemy_army_gas += gas_value

    async def update_own_army_value(self):
        self.own_army_value_minerals = 0
        self.own_army_value_gas = 0

        for unit in self.ai.units:
            if not self.unit_values.is_worker(unit.type_id):
                self.own_army_value_minerals += self.unit_values.minerals(unit.type_id)
                self.own_army_value_gas += self.unit_values.gas(unit.type_id)

    async def predict_enemy_composition(self):
        if self.knowledge.enemy_race == Race.Random:
            return  # let's wait until we know the actual race.

        guesser = CompositionGuesser(self.knowledge)
        guesser.left_minerals = self.predicted_enemy_free_minerals
        guesser.left_gas = self.predicted_enemy_free_gas

        additional_guess: List[UnitCount] = guesser.predict_enemy_composition()
        for unit_count in additional_guess:
            existing = self.find(self.predicted_enemy_composition, unit_count.enemy_type)
            if existing is None:
                self.predicted_enemy_composition.append(unit_count)
            else:
                existing.count += unit_count.count

    def find(self, lst: List[UnitCount], enemy_type) -> Optional[UnitCount]:
        for unit_count in lst:
            if unit_count.enemy_type == enemy_type:
                return unit_count
        return None

    async def post_update(self):
        await self.debug_message()

    async def debug_message(self):
        if self.knowledge.my_race == Race.Protoss:
            # my_comp = self.enemy_build.gate_type_values(self.predicted_enemy_composition)
            # my_comp.extend(self.enemy_build.robo_type_values(self.predicted_enemy_composition))
            # my_comp.extend(self.enemy_build.star_type_values(self.predicted_enemy_composition))

            enemy_comp = sorted(self.predicted_enemy_composition, key=lambda uc: uc.count, reverse=True)
            # my_comp = sorted(my_comp, key=lambda c: c.count, reverse=True)

            if self.debug:
                client: Client = self.ai._client
                msg = f"Us vs them: {self.own_value} / {self.enemy_value}\n"
                msg += f"Known enemy army (M/G): {self.enemy_army_known_minerals} / {self.enemy_army_known_gas}\n"
                msg += f"Enemy predicted money (M/G): {self.predicted_enemy_free_minerals} / {self.predicted_enemy_free_gas}\n"

                msg += f"\nComposition:\n"

                for unit_count in enemy_comp:
                    msg += f" {unit_count.to_short_string()}"

                # msg += f"\nCounter:\n"

                # for unit_count in my_comp:
                #     if unit_count.count > 0:
                #         msg += f" {unit_count.to_string()}\n"

                client.debug_text_2d(msg, Point2((0.1, 0.1)), None, 16)
