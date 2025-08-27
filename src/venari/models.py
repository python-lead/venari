import datetime
import pprint
from typing import Optional, List, Dict

from pydantic import BaseModel, HttpUrl


class SalaryRange(BaseModel):
    """
    Stores salary range as currency per hour
    """

    min: Optional[int] = None
    max: Optional[int] = None
    currency: Optional[str] = "PLN"

    def as_monthly(self) -> tuple[Optional[int], Optional[int]]:
        """Convert hourly salary to monthly using 160 working hours/month."""
        min_monthly = self.min * 160 if self.min is not None else None
        max_monthly = self.max * 160 if self.max is not None else None
        return min_monthly, max_monthly

    def hourly(self) -> str:
        return f"{self.min}-{self.max} {self.currency}/h"

    def monthly(self) -> str:
        min, max = self.as_monthly()
        return f"{min}-{max} {self.currency}/M"


class JobOfferDetails(BaseModel):
    organisation_info: Optional[str]
    tech_stack: Optional[Dict[str, str]]
    job_summary: Optional[str]
    published_date: Optional[datetime.date]
    source_url: Optional[HttpUrl]

    def display(self) -> None:
        print("TECH STACK:")
        pprint.pp(self.tech_stack, compact=True)
        print("\nSUMMARY:")
        pprint.pp(self.job_summary, compact=True)


class JobOffer(BaseModel):
    title: Optional[str]
    url: Optional[HttpUrl]
    organisation_name: Optional[str]
    location: Optional[str]
    raw_span_data: List[str]
    logo: Optional[HttpUrl] = None
    remote: Optional[bool] = False
    salary: Optional[SalaryRange] = None
    details: Optional[JobOfferDetails] = None

    def __repr__(self) -> str:
        if self.salary:
            return f"{self.salary.hourly()} {self.title} @ {self.organisation_name} [{self.location}]"
        return f"{self.title} @ {self.organisation_name} [{self.location}]"

    def display(self) -> None:
        print(f"{self.title} @ {self.organisation_name} - {self.salary.monthly()}")
