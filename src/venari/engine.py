import asyncio
from logging import Logger
from typing import List

from venari.engine_interface import EngineInterface
from venari.models import JobOffer
from venari.offer_filters import FilterInterface
from vendors.scrapper_interfaces import OfferScrapperInterface


class Engine(EngineInterface):
    """
    Scrapper execution engine
    todo:
    - todo: implement support for multiple scrappers
    """

    def __init__(
        self, logger: Logger, scrapper: OfferScrapperInterface, skip_details=False
    ) -> None:
        self.logger = logger
        self.offer_filters: List[FilterInterface] = []
        self.scrapper = scrapper
        self._skip_details = skip_details

    async def execute(self) -> None:
        self.offers = await self._get_offers()
        self.filter_offers()
        self.filtered_offers = self._order_offers(self.filtered_offers)
        self._display_offers()

    async def _get_offers(self) -> list[JobOffer]:
        """
        Fetch all offers from the configured scrapper along with details
        Result offer list order is based on completion time, not the original order
        - todo: Implement task timeout support
        """

        async def wrap_offers(offer: JobOffer):
            """
            Helper coroutine that keeps offer and details together while tasks are completed
            Simplifies result collection
            """
            return offer, await self.scrapper.get_offer_details(offer)

        self.logger.info("Scrapping offers")
        offers = await self.scrapper.get_offers()

        if self._skip_details:
            self.logger.info("Skipping scrapping offer details")
            return list(offers)

        self.logger.info("Scrapping offer details")
        tasks = [asyncio.create_task(wrap_offers(offer)) for offer in offers]

        complete_offers = []
        for task in asyncio.as_completed(tasks):
            offer, details = await task
            offer.details = details
            complete_offers.append(offer)

        return complete_offers

    def _display_offers(self):
        self.logger.info(
            f"Displaying acceptable offers - "
            f"{f'{len(self.filtered_offers)} out of {len(self.offers)}' if self.filtered_offers else 'No offers'}"
        )

        if self.filtered_offers:
            if self._skip_details:
                for offer in self.filtered_offers:
                    offer.display()
            else:
                for offer in self.filtered_offers:
                    offer.display()

    def _order_offers(self, offers: List[JobOffer]) -> List[JobOffer]:
        """
        Orders job offers by their maximum salary in descending order
        # todo: Move to interface, allow ordering key as init param
        """
        return sorted(
            offers,
            key=self._upper_offer_salary,
            reverse=True,
        )

    @staticmethod
    def _upper_offer_salary(offer: JobOffer) -> float:
        """
        Returns the upper salary bound for sorting
        """
        if not getattr(offer, "salary", None):
            return float(-1)

        max_salary = getattr(offer.salary, "max", None)
        return max_salary if max_salary is not None else float(-1)
