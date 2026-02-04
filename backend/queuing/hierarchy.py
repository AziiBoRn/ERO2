from abc import ABC, abstractmethod
from common.model import *
from pandas import DataFrame

class QueueSystem(ABC):
    @property
    def name(self) -> str:
        pass

    @property
    def description(self) -> str:
        pass

    @property
    def architecture_type(self) -> ArchitectureType:
        pass

    @abstractmethod
    def process(self, inp : Input) -> tuple[DataFrame, DataFrame]:
        pass