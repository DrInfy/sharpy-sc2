from abc import abstractmethod, ABC


class IDataManager(ABC):
    @abstractmethod
    def set_build(self, build_name: str):
        pass
