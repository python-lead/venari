from logging import Logger
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from venari.models import JobOffer, SalaryRange
from vendors.parser_interfaces import OfferParserInterface
from vendors.utils import try_int


class JustJoinItParser(OfferParserInterface):
    def __init__(self, base_url: str, logger: Logger) -> None:
        self.BASE_URL = base_url
        self.logger = logger

    async def parse_offers(self, content: str) -> list[JobOffer]:
        soup = BeautifulSoup(content, "html.parser")
        offers: List[JobOffer] = []

        for offer in soup.select("a.offer-card"):
            relative_url = offer.get("href")
            full_url = urljoin(self.BASE_URL, relative_url)

            title_tag = offer.select_one("h3")
            title = title_tag.text.strip() if title_tag else None

            logo_tag = offer.select_one("img")
            logo_url = logo_tag.get("src") if logo_tag else None

            span_data = [x.get_text(strip=True) for x in offer.select("span")]

            job_offer = self._get_span_data(
                span_data=span_data, title=title, url=full_url, logo_url=logo_url
            )
            offers.append(job_offer)

        return offers

    def _get_span_data(
        self,
        span_data: List[str],
        title: Optional[str],
        url: str,
        logo_url: Optional[str],
    ) -> JobOffer:
        salary = None
        org = loc = None
        remote = False

        remainder = span_data

        # Check for salary in first 3 items
        if len(span_data) >= 3 and try_int(span_data[0]) and try_int(span_data[1]):
            raw_min = try_int(span_data[0])
            raw_max = try_int(span_data[1])
            unit = span_data[2]
            h_min, h_max = self._to_hourly(raw_min, raw_max, unit)
            if h_min and h_max:
                salary = SalaryRange(min=h_min, max=h_max, currency="PLN")
            else:
                # todo: figure out why data is missing even if condition is met
                self.logger.warning(f"Missing salary range for: {title}")
                salary = None
            remainder = span_data[3:]

        if remainder:
            org = remainder[0]
        if len(remainder) > 1:
            loc = remainder[1]
        if any("remote" in x.lower() for x in remainder):
            remote = True

        return JobOffer(
            title=title,
            url=url,
            logo=logo_url,
            organisation_name=org,
            location=loc,
            remote=remote,
            salary=salary,
            raw_span_data=span_data,
        )

    @staticmethod
    def _to_hourly(
        min_val: int, max_val: int, unit: str
    ) -> tuple[Optional[int], Optional[int]]:
        """Converts salary to hourly if unit is monthly."""
        if "/month" in unit.lower():
            return min_val // 160, max_val // 160
        elif "/h" in unit.lower():
            return min_val, max_val
        return None, None
