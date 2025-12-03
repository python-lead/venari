import asyncio
from logging import Logger
from time import perf_counter
from typing import List

from venari.engine_interface import EngineInterface
from venari.models import JobOffer
from venari.offer_filters import FilterInterface
from vendors.scrapper_interfaces import OfferScrapperInterface

import webbrowser


class Engine(EngineInterface):
    """
    Scrapper execution engine
    """

    def __init__(
        self,
        logger: Logger,
        scrapper: OfferScrapperInterface,
        skip_details=False,
        order_offers: bool = True,
        open_offers_in_browser: bool = False,
        display_offers: bool = False,
    ) -> None:
        self.logger = logger
        self.offer_filters: List[FilterInterface] = []
        self.scrapper = scrapper
        self._skip_details = skip_details
        self._open_offers_in_browser = open_offers_in_browser
        self._order_offers = order_offers
        self._display_offers = display_offers

    async def execute(self) -> None:
        self.offers = await self._get_offers()
        self.filter_offers()
        if self._order_offers:
            self.filtered_offers = self._order_filtered_offers(self.filtered_offers)
        if self._display_offers:
            self.display_offers()

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

        _t1_start = perf_counter()
        complete_offers = []
        for task in asyncio.as_completed(tasks):
            offer, details = await task
            offer.details = details
            complete_offers.append(offer)
        _t1_stop = perf_counter()

        self.logger.info(
            f"Elapsed time: {_t1_stop - _t1_start:.2f} seconds. Offers processed: {len(complete_offers)}"
        )
        return complete_offers

    def display_offers(self):
        self.logger.info(
            f"Displaying acceptable offers - "
            f"{f'{len(self.filtered_offers)} out of {len(self.offers)}' if self.filtered_offers else 'No offers'}"
        )

        if self.filtered_offers:
            for offer in self.filtered_offers:
                offer.display()

                if self._open_offers_in_browser:
                    self._open_browser_page_test(str(offer.url))

        self.logger.info(
            f"Displayed acceptable offers - "
            f"{f'{len(self.filtered_offers)} out of {len(self.offers)}' if self.filtered_offers else 'No offers'}"
        )

    def _order_filtered_offers(self, offers: List[JobOffer]) -> List[JobOffer]:
        """
        Orders job offers by their maximum salary in descending order
        """
        self.logger.info("Ordering offers by max salary")
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

    @staticmethod
    def _open_browser_page_test(url: str) -> None:
        webbrowser.open_new_tab(url)
