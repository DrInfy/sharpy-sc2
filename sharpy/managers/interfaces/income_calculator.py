from abc import abstractmethod, ABC


class IIncomeCalculator(ABC):
    @property
    @abstractmethod
    def mineral_income(self) -> float:
        pass

    @property
    @abstractmethod
    def gas_income(self) -> float:
        pass
