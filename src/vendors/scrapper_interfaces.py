from abc import abstractmethod, ABC
from typing import Iterator

from venari.models import JobOffer, JobOfferDetails


class OfferScrapperInterface(ABC):
    @abstractmethod
    async def get_offers(self) -> Iterator[JobOffer]:
        ...

    @abstractmethod
    async def get_offer_details(self, offer: JobOffer) -> JobOfferDetails:
        ...
