from datetime import datetime
from logging import Logger
from typing import List, Optional
from urllib.parse import urljoin
import re

from bs4 import BeautifulSoup

from venari.models import JobOffer, SalaryRange, JobOfferDetails
from vendors.parser_interfaces import OfferParserInterface
from vendors.utils import try_int, convert_salary_to_hourly_range


class JustJoinItParser(OfferParserInterface):
    ACCEPTABLE_LEVELS = {
        "nice to have",
        "regular",
        "advanced",
        "junior",
        "master",
        "c1",
        "c2",
        "b2",
        "a1",
        "a2",
        "b1",
    }

    def __init__(self, base_url: str, logger: Logger) -> None:
        self.BASE_URL = base_url
        self.logger = logger
        # Contains values from tech stack that were not accepted.
        self.rejected_tech_stack_values: set[tuple[str, str]] = set()

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

            org_tag = offer.select_one(
                "p.MuiTypography-root.MuiTypography-body1.mui-1jo71uz"
            )
            if org_tag:
                organisation_name = org_tag.get_text(strip=True)
            else:
                organisation_name = None
                self.logger.warning(f"Org tag not found for: {title}")

            span_data = [x.get_text(strip=True) for x in offer.select("span")]

            job_offer = self._get_span_data(
                span_data=span_data,
                title=title,
                url=full_url,
                logo_url=logo_url,
                organisation_name=organisation_name,
            )
            offers.append(job_offer)

        if not offers:
            self.logger.info(f"{self.__class__.__name__}: Detected a page with no offers!")

        return offers

    def _get_span_data(
        self,
        span_data: List[str],
        title: Optional[str],
        url: str,
        logo_url: Optional[str],
        organisation_name: Optional[str],
    ) -> JobOffer:
        salary = None
        loc = None
        remote = False

        remainder = span_data

        # Check for salary in first 3 items
        if (
            len(span_data) >= 3
            and try_int(span_data[1]) is not None
            and try_int(span_data[2]) is not None
        ):
            raw_min = try_int(span_data[1])
            raw_max = try_int(span_data[2])
            unit = span_data[3]
            h_min, h_max = convert_salary_to_hourly_range(raw_min, raw_max, unit)
            if h_min and h_max:
                salary = SalaryRange(min=h_min, max=h_max, currency="PLN")
            else:
                self.logger.warning(f"Missing salary range for: {title} - {span_data}")
                salary = None
            remainder = span_data[3:]

        if len(remainder) > 1:
            loc = remainder[1]
        if any("remote" in x.lower() for x in remainder):
            remote = True

        return JobOffer(
            title=title,
            url=url,
            logo=logo_url,
            organisation_name=organisation_name,
            location=loc,
            remote=remote,
            salary=salary,
            raw_span_data=span_data,
        )

    async def parse_details(
        self, content: str, url: Optional[str] = None, offer: Optional[JobOffer] = None
    ) -> JobOfferDetails:
        """
        Parse detailed information from a job offer page
        Current implementation supports parsing job postings based on templates observed at Aug 2025
        """
        soup = BeautifulSoup(content, "html.parser")
        full_text = soup.get_text(separator="\n", strip=True)

        # Extract organisation info
        org_section = None
        pattern = r"Meet the company\s*(.*?)\s*(?:Company profile|Office location)"
        match = re.search(pattern, full_text, flags=re.DOTALL | re.IGNORECASE)
        if match:
            org_section = match.group(1).strip()

        # Trim organisation name if duplicated at start
        if offer and offer.organisation_name and org_section:
            prefix = f"{offer.organisation_name}\n"
            if org_section.startswith(prefix):
                org_section = org_section[len(prefix) :].lstrip()

        # Extract raw tech stack pairs
        raw_stack = []
        for container in soup.find_all("div"):
            tech_name = container.find("h4")
            level = container.find("span")
            if tech_name and level:
                raw_stack.append(
                    (tech_name.get_text(strip=True), level.get_text(strip=True))
                )

        # Clean and normalize tech stack
        tech_stack: dict[str, str] = {}
        for tech, level in raw_stack:
            tech_clean = tech.strip()
            level_clean = level.strip().lower()
            if level_clean in self.ACCEPTABLE_LEVELS:
                tech_stack[tech_clean] = level_clean  # overwrite duplicates
            else:
                self.rejected_tech_stack_values.add((tech_clean, level.strip()))

        # Extract job summary
        job_summary = None
        summary_match = re.search(
            r"Job description(.*?)(Published:\s*\d{2}\.\d{2}\.\d{4})",
            full_text,
            re.DOTALL,
        )
        if summary_match:
            block = summary_match.group(1).strip()
            # Keep formatting (including bullets and line breaks)
            summary_ending_index = block.find("Tech stack\n")
            if summary_ending_index:
                job_summary = block[:summary_ending_index]
            else:
                job_summary = block

        # Extract published date separately
        published_date = None
        pub_match = re.search(r"Published:\s*(\d{2}\.\d{2}\.\d{4})", full_text)
        if pub_match:
            published_date = datetime.strptime(pub_match.group(1), "%d.%m.%Y").date()

        return JobOfferDetails(
            organisation_info=org_section,
            tech_stack=tech_stack,
            job_summary=job_summary,
            published_date=published_date,
            source_url=url,
        )
