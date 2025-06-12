from logging import Logger
from typing import List

from venari.engine_interface import EngineInterface
from venari.models import JobOffer
from venari.offer_filters import FilterInterface
from vendors.justjoinit.scrapper import JustJoinItScrapper


class Engine(EngineInterface):
    """
    Scrapper execution engine
    """

    def __init__(self, logger: Logger) -> None:
        self.logger = logger
        self.offers: list[JobOffer] | None = None
        # todo: include ability to add filter backends for offers
        self.offer_filters: List[FilterInterface] = []

    async def execute(self) -> None:
        # todo: implement better support for multiple scrappers
        scrapper = JustJoinItScrapper(logger=self.logger)
        self.offers = await scrapper.get_offers()
        self.filter_offers()
        self.display_offers()

    def display_offers(self):
        self.logger.info("Displaying offers")
        print(f"Scrapped offers - {len(self.offers)}")
        for offer in self.offers:
            print(f"\t{repr(offer)}")
