from abc import ABC, abstractmethod
from logging import Logger
from typing import List, Type, Sequence

from venari.models import JobOffer
from venari.offer_filters import FilterInterface


class EngineInterface(ABC):
    logger: Logger
    offers: list[JobOffer] | None
    offer_filters: List[Type[FilterInterface]]

    @abstractmethod
    async def execute(self) -> None:
        ...

    def add_filters(self, filters: Sequence[Type[FilterInterface]]) -> None:
        self.offer_filters.extend(filters)

    def filter_offers(self) -> None:
        if self.offer_filters:
            self.offers = [
                offer for offer in self.offers
                if all(filter_backend.filter_offer(offer) for filter_backend in self.offer_filters)
            ]

    def clear_offer_filters(self) -> None:
        self.offer_filters.clear()
