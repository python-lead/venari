from abc import ABC, abstractmethod


class EngineInterface(ABC):
    @abstractmethod
    async def execute(self) -> None:
        pass
