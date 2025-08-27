from logging import Logger

import httpx

from venari.models import JobOffer, JobOfferDetails
from vendors.justjoinit.parsers import JustJoinItParser
from vendors.scrapper_interfaces import OfferScrapperInterface


class JustJoinItScrapper(OfferScrapperInterface):
    def __init__(self, logger: Logger):
        self.logger = logger
        self.BASE_URL = "https://justjoin.it"
        self._OFFER_PAGE_URL = (
            "https://justjoin.it/job-offers/all-locations/python?remote=yes&from=1"
        )
        self.offer_parser = JustJoinItParser(base_url=self.BASE_URL, logger=logger)

    async def get_offers(self) -> list[JobOffer]:
        offer_page = await self._fetch_content_page(url=self._OFFER_PAGE_URL)
        return await self.offer_parser.parse_offers(content=offer_page)

    async def get_offer_details(self, offer: JobOffer) -> JobOfferDetails:
        detail_page = await self._fetch_content_page(url=str(offer.url))
        details = await self.offer_parser.parse_details(content=detail_page, url=offer.url, offer=offer)
        details.source_url = offer.url
        details.display()
        return details

    @staticmethod
    async def _fetch_content_page(url) -> str:
        # todo: shouldn't be a scrapper method. Add client for communication in constructor
        # todo: add exception handling
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.text
