import asyncio
from logging import Logger

import httpx

from venari.models import JobOffer, JobOfferDetails
from vendors.justjoinit.parsers import JustJoinItParser
from vendors.scrapper_interfaces import OfferScrapperInterface


class JustJoinItScrapper(OfferScrapperInterface):
    BASE_URL = "https://justjoin.it"
    # todo: should support more than python jobs
    _PATH = "/job-offers/all-locations/python"

    def __init__(
        self,
        logger: Logger,
        max_pages: int = 1,
        timeout: float = 10.0,
        max_retries: int = 5,
    ):
        """
        :param max_pages: Number of pages to fetch when scraping offers
        :param timeout: HTTP client timeout in seconds
        """
        self.logger = logger
        self.max_pages = max_pages
        self.timeout = timeout
        self.max_retries = max_retries
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
        """
        detail_page = await self._fetch_content_page(url=str(offer.url))
        details = await self.offer_parser.parse_details(
            content=detail_page, url=offer.url, offer=offer
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
        Fetches raw HTML content from the given URL with retry logic on timeout errors
        Retries up to self.max_retries times on httpx.ReadTimeout
        # todo: shouldn't be a scrapper method. Add client for communication in constructor
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(
                    follow_redirects=True, timeout=self.timeout
                ) as client:
                    response = await client.get(url)
                    response.raise_for_status()
                    return response.text

            except (httpx.ReadTimeout, httpx.ConnectError, httpx.ConnectTimeout) as e:
                self.logger.debug(
                    f"Timeout while fetching URL: {url} "
                    f"(attempt {attempt}/{self.max_retries}). "
                    f"Error: {e}"
                )

                if attempt == self.max_retries:
                    raise

                # Throttling retry attempts
                await asyncio.sleep(1 * attempt)

            except httpx.HTTPError as e:
                # You may choose to retry only on timeouts, not on all errors.
                self.logger.error(
                    f"HTTP error while fetching URL: {url}. Not retrying. Error: {e}"
                )
                raise
