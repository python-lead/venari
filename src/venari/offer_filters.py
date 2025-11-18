import logging
from abc import ABC
from typing import Set

from venari.models import JobOffer

logger = logging.getLogger(__name__)


class FilterInterface(ABC):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        return True


class FilterTechRequirementsBase(FilterInterface, ABC):
    """
    Base filter for tech requirement and title-based filters.

    Subclasses should define:
    - `filtered_requirements`: a set of lowercase tech keywords to exclude from offer details
    - `filtered_titles`: a set of lowercase keywords to exclude from offer titles
    """

    filtered_requirements: Set[str] = set()
    filtered_titles: Set[str] = set()

    @classmethod
    def filter_offer(cls, offer: JobOffer) -> bool:
        """
        Returns False if offer matches any filtered requirement or filtered title.
        """
        # Filter by tech stack (requirements)
        if offer.details:
            tech_stack_lower = {
                requirement.lower() for requirement in offer.details.tech_stack.keys()
            }

            if tech_stack_lower:
                rejected_requirements = cls.filtered_requirements.intersection(
                    tech_stack_lower
                )
                if rejected_requirements:
                    logger.debug(
                        f"{cls.__name__} skipped (tech stack): {offer.title} - {rejected_requirements}"
                    )
                    return False

        # Filter by title
        if cls.filtered_titles:
            title_lower = offer.title.lower()
            for keyword in cls.filtered_titles:
                if keyword in title_lower:
                    logger.debug(
                        f"{cls.__name__} skipped (title): {offer.title} - keyword '{keyword}'"
                    )
                    return False

        return True


class MinimumWage100(FilterInterface):
    @classmethod
    def filter_offer(cls, offer: JobOffer) -> bool:
        """
        Only filters wages if salary is available
        """
        if offer.salary and offer.salary.min < 100:
            logger.debug(
                f"{cls.__name__} skipped: {offer.title} - salary {offer.salary.hourly()} | {offer.salary.monthly()}"
            )
            return False

        return True


class ImpostorSyndromeFilter(FilterInterface):
    @classmethod
    def filter_offer(cls, offer: JobOffer) -> bool:
        if offer.salary and offer.salary.min > 160:
            logger.debug(
                f"{cls.__name__} skipped: {offer.title} - salary {offer.salary.hourly()} | {offer.salary.monthly()}"
            )
            return False

        return True


class KnownSalary(FilterInterface):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        """
        Filters out offers without disclosed salary
        """
        return offer.salary is not None


class IgnoreFrontendStack(FilterTechRequirementsBase):
    filtered_titles = {"fullstack", "full stack", "full-stack"}
    filtered_requirements = {
        "node.js",
        "javascript",
        "vue.js",
        "typescript",
        "react",
    }


class IgnoreNonPythonBackends(FilterTechRequirementsBase):
    filtered_requirements = {"kotlin", "go", "java", "scala"}


class IgnoreAIOffers(FilterTechRequirementsBase):
    filtered_requirements = {"ai", "ml", "ai/ml"}
    filtered_titles = {"ai", "machine learning", "data scientist"}


class IgnoreBigData(FilterTechRequirementsBase):
    filtered_requirements = {
        "etl",
        "spark",
        "databricks",
        "bigquery",
        "big data",
        "snowflake",
    }
    filtered_titles = {"data engineering"}


class IgnoreRobotics(FilterTechRequirementsBase):
    filtered_requirements = {"ros"}
    filtered_titles = {"robotics"}
