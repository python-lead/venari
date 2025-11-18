from abc import ABC, abstractmethod
from logging import Logger
from typing import List, Type, Sequence

from venari.models import JobOffer
from venari.offer_filters import FilterInterface


class EngineInterface(ABC):
    logger: Logger
    offers: list[JobOffer] | None = None
    filtered_offers: list[JobOffer] | None = None
    rejected_offers: list[JobOffer] | None = None
    offer_filters: List[Type[FilterInterface]]

    @abstractmethod
    async def execute(self) -> None: ...

    def add_filters(self, filters: Sequence[Type[FilterInterface]]) -> None:
        """Register one or more filter classes (not instances)."""
        if not hasattr(self, "offer_filters") or self.offer_filters is None:
            self.offer_filters = []
        self.offer_filters.extend(filters)

    def filter_offers(self) -> None:
        """
        Filter offers by registered filters
        """
        if not self.offers:
            self.logger.warning("No offers to filter")
            self.filtered_offers, self.rejected_offers = [], []
            return

        if not self.offer_filters:
            self.logger.info("No filters registered, skipping filtering")
            self.filtered_offers = self.offers
            self.rejected_offers = []
            return

        self.logger.info(
            f"Filtering offers using filters: {[cls.__name__ for cls in self.offer_filters]}"
        )

        filtered = []
        rejected = []

        for offer in self.offers:
            rejected_by: list[str] = []

            for filter_cls in self.offer_filters:
                try:
                    if not filter_cls.filter_offer(offer):
                        rejected_by.append(filter_cls.__name__)
                except Exception as exc:
                    self.logger.exception(
                        f"Filter {filter_cls.__name__} failed for {offer}: {exc}"
                    )
                    rejected_by.append(filter_cls.__name__)

            if rejected_by:
                offer.rejected_by = rejected_by
                rejected.append(offer)
            else:
                filtered.append(offer)

        self.filtered_offers = filtered
        self.rejected_offers = rejected

        self.logger.info(
            f"Filtering complete: accepted={len(filtered)}, rejected={len(rejected)}"
        )
