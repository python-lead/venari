import asyncio
from logging import Logger

from connectors.http_clients.http_client_interfaces import AsyncHttpClientInterface
from connectors.http_clients.httpx_client import HttpxClient
from venari.models import JobOffer, JobOfferDetails
from vendors.justjoinit.parsers import JustJoinItParser
from vendors.scrapper_interfaces import OfferScrapperInterface


class JustJoinItScrapper(OfferScrapperInterface):
    """
    JustJoinIt scrapper

    todo:
    - should support more than python jobs
    - add exception handling support for self._fetch_content_page. Exception should terminate scrapping
    - refactor get_offers and get_offer_details - parsers should start work as soon as the resource is fetched
    - add tracking_id support
    """

    BASE_URL = "https://justjoin.it"
    _PATH = "/job-offers/all-locations/python"

    def __init__(
        self,
        logger: Logger,
        max_pages: int = 1,
        client: AsyncHttpClientInterface = HttpxClient,
    ):
        """
        :param max_pages: Number of pages to fetch when scraping offers
        """
        self.logger = logger
        self.client = client
        self.max_pages = max_pages
        self.offer_parser = JustJoinItParser(base_url=self.BASE_URL, logger=logger)

    async def get_offers(self) -> list[JobOffer]:
        tasks = [
            self._fetch_content_page(self._build_offers_page_url(page * 100))
            for page in range(0, self.max_pages)
        ]
        pages = await asyncio.gather(*tasks)

        offers: list[JobOffer] = []
        for content in pages:
            offers.extend(await self.offer_parser.parse_offers(content=content))
        return offers

    async def get_offer_details(self, offer: JobOffer) -> JobOfferDetails:
        """
        Fetch and parse offer details

        todo:
        - parsing details can be done for already fetched detail pages? Keeping order might be problematic
        """
        detail_page = await self._fetch_content_page(url=str(offer.url))
        details = await self.offer_parser.parse_details(
            content=detail_page, url=str(offer.url), offer=offer
        )
        details.source_url = offer.url
        return details

    def _build_offers_page_url(self, from_value: int) -> str:
        """
        Build a URL for a specific page number of the offer listing
        """
        url = (
            f"{self.BASE_URL}{self._PATH}"
            f"?remote=yes&from={from_value}&orderBy=DESC&sortBy=newest"
        )
        self.logger.info(
            f"Preparing request url for offers from : {from_value}\n -> {url}"
        )

        return url

    async def _fetch_content_page(self, url: str) -> str:
        """
        Fetches raw HTML content from the given URL using provided async http client

        todo:
        - shouldn't be a scrapper method. Add client for communication in constructor
        """
        response = await self.client.get(url, tracking_id=None)
        return response.text
