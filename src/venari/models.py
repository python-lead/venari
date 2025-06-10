from typing import Optional, List
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


class JobOffer(BaseModel):
    title: Optional[str]
    url: Optional[HttpUrl]
    logo: Optional[HttpUrl]

    organisation_name: Optional[str]
    location: Optional[str]
    remote: Optional[bool] = False

    salary: Optional[SalaryRange]

    raw_span_data: List[str]

    def __repr__(self) -> str:
        if self.salary:
            return f"{self.salary.hourly()} {self.title} @ {self.organisation_name} [{self.location}]"
        return f"{self.title} @ {self.organisation_name} [{self.location}]"
