from logging import Logger

import httpx

from venari.models import JobOffer
from vendors.justjoinit.parsers import JustJoinItParser


class JustJoinItScrapper:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.BASE_URL = "https://justjoin.it"
        self._OFFER_PAGE_URL = "https://justjoin.it/job-offers/all-locations/python?remote=yes&from=1"
        self.offer_parser = JustJoinItParser(base_url=self.BASE_URL, logger=logger)

    async def get_offers(self) -> list[JobOffer]:
        offer_page = await self.fetch_job_page()
        return await self.offer_parser.parse_offers(content=offer_page)

    async def fetch_job_page(self) -> str:
        # todo: add exception handling
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            response = await client.get(self._OFFER_PAGE_URL)
            response.raise_for_status()
            return response.text
