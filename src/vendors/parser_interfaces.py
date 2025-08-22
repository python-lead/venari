from abc import abstractmethod, ABC
from typing import Iterator

from venari.models import JobOfferDetails


class OfferParserInterface(ABC):
    @abstractmethod
    async def parse_offers(self, content: str) -> Iterator[dict]:
        ...

    @abstractmethod
    async def parse_details(self, content: str) -> JobOfferDetails:
        ...
