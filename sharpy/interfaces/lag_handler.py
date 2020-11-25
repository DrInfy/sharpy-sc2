from abc import abstractmethod


class ILagHandler:
    @abstractmethod
    def step_took(self, ms: float):
        pass
