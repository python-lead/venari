from abc import ABC, abstractmethod
from typing import Protocol, Optional


class Response(Protocol):
    @property
    @abstractmethod
    def text(self) -> str: ...


class AsyncHttpClientInterface(ABC):
    @abstractmethod
    async def get(self, url: str, tracking_id: Optional[str]) -> Response: ...
