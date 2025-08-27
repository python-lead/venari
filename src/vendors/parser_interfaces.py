from abc import abstractmethod, ABC
from typing import Iterator, Optional

from pydantic import HttpUrl

from venari.models import JobOfferDetails, JobOffer


class OfferParserInterface(ABC):
    @abstractmethod
    async def parse_offers(self, content: str) -> Iterator[dict]: ...

    @abstractmethod
    async def parse_details(
        self, content: str, url: Optional[HttpUrl], offer: Optional[JobOffer]
    ) -> JobOfferDetails: ...
