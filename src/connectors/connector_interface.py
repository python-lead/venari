from abc import abstractmethod
from typing import Protocol


class ConnectorInterface(Protocol):
    @abstractmethod
    async def terminate(self) -> None:
        pass
