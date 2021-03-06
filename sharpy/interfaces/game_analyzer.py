from abc import ABC, abstractmethod

from typing import TYPE_CHECKING

from sharpy.general.extended_power import ExtendedPower

if TYPE_CHECKING:
    from sharpy.managers.extensions.game_states import Advantage, AirArmy


class IGameAnalyzer(ABC):
    @property
    @abstractmethod
    def our_power(self) -> ExtendedPower:
        pass

    @property
    @abstractmethod
    def enemy_power(self) -> ExtendedPower:
        pass

    @property
    @abstractmethod
    def enemy_predict_power(self) -> ExtendedPower:
        pass

    @property
    @abstractmethod
    def our_income_advantage(self) -> "Advantage":
        pass

    @property
    @abstractmethod
    def our_army_predict(self) -> "Advantage":
        pass

    @property
    @abstractmethod
    def our_army_advantage(self) -> "Advantage":
        pass

    @property
    @abstractmethod
    def enemy_air(self) -> "AirArmy":
        pass

    @property
    @abstractmethod
    def army_at_least_clear_disadvantage(self) -> bool:
        pass

    @property
    @abstractmethod
    def army_at_least_small_disadvantage(self) -> bool:
        pass

    @property
    @abstractmethod
    def army_at_least_clear_advantage(self) -> bool:
        pass

    @property
    @abstractmethod
    def army_at_least_small_advantage(self) -> bool:
        pass

    @property
    @abstractmethod
    def army_at_least_advantage(self) -> bool:
        pass

    @property
    @abstractmethod
    def army_can_survive(self) -> bool:
        pass

    @property
    @abstractmethod
    def predicting_victory(self) -> bool:
        pass

    @property
    @abstractmethod
    def been_predicting_defeat_for(self) -> float:
        pass

    @property
    @abstractmethod
    def predicting_defeat(self) -> bool:
        pass
