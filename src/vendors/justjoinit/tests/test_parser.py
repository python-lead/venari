import pytest
from pathlib import Path
from typing import List

from venari.models import JobOffer, SalaryRange
import logging

from vendors.justjoinit.parsers import JustJoinItParser


class TestJustJoinItParser:
    BASE_URL = "https://justjoin.it"
    DATA_DIR = Path(__file__).parent / "data"

    @pytest.fixture(scope="class")
    def logger(self):
        return logging.getLogger("test")

    @pytest.fixture
    def parser(self, logger):
        return JustJoinItParser(base_url=self.BASE_URL, logger=logger)

    def load_html(self, filename: str) -> str:
        path = self.DATA_DIR / filename
        return path.read_text(encoding="utf-8")

    @pytest.mark.asyncio
    async def test_offer_with_full_salary(self, parser: JustJoinItParser):
        html = self.load_html("offer_with_full_salary.html")
        offers: List[JobOffer] = await parser.parse_offers(html)

        assert len(offers) == 1
        offer = offers[0]

        assert offer.title == "Python Developer"
        assert str(offer.url).endswith("/offers/python-dev")
        assert str(offer.logo) == "https://logo.com/python.svg"
        assert offer.organisation_name == "CoolCompany"
        assert offer.location == "Warszawa"
        assert offer.remote is True
        assert offer.salary == SalaryRange(min=187, max=375, currency="PLN")
        assert offer.raw_span_data[2] == "PLN/month"

    @pytest.mark.asyncio
    async def test_offer_without_salary(self, parser: JustJoinItParser):
        html = self.load_html("offer_without_salary.html")
        offers: List[JobOffer] = await parser.parse_offers(html)

        assert len(offers) == 1
        offer = offers[0]
        assert offer.salary is None
        assert offer.organisation_name == "NoSalaryCorp"

    @pytest.mark.asyncio
    async def test_offer_partial_salary(self, parser: JustJoinItParser):
        html = self.load_html("offer_partial_salary.html")
        offers: List[JobOffer] = await parser.parse_offers(html)

        assert len(offers) == 1
        offer = offers[0]
        assert offer.salary is None

    @pytest.mark.asyncio
    async def test_real_offers(self, parser: JustJoinItParser):
        html = self.load_html("content.html")
        offers: List[JobOffer] = await parser.parse_offers(html)

        assert len(offers) == 2

        assert offers[0].salary.hourly() == "134-166 PLN/h"
        assert offers[0].title == "Python Developer (with ML/AI)"
        assert offers[1].salary.hourly() == "110-130 PLN/h"
        assert offers[1].title == "Python Developer with German"
