import logging
from abc import ABC
from typing import Set

from venari.models import JobOffer

logger = logging.getLogger(__name__)


class FilterInterface(ABC):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        return True


class MinimumWage100(FilterInterface):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        """
        Only filters wages if salary is available
        """
        if offer.salary and offer.salary.min < 100:
            logger.debug(
                f"MinimumWage100 skipped: {offer.title} - salary {offer.salary.hourly()} | {offer.salary.monthly()}"
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


class FilterTechRequirementsBase(FilterInterface, ABC):
    """
    Base filter for tech requirement filters
    filtered_requirements property should consist of lowercase string values
    """

    filtered_requirements: Set[str]

    @classmethod
    def filter_offer(cls, offer: JobOffer) -> bool:
        """ """
        if offer.details:
            tech_stack_lower = {
                requirement.lower() for requirement in offer.details.tech_stack.keys()
            }

            if tech_stack_lower:
                rejected_requirements = set.intersection(
                    cls.filtered_requirements, tech_stack_lower
                )
                if rejected_requirements:
                    logger.debug(
                        f"{cls.__name__} skipped: {offer.title} - {rejected_requirements}"
                    )

                    return False

        return True


class IgnoreFrontendStack(FilterTechRequirementsBase):
    filtered_requirements = {"node.js", "javascript", "vue.js"}


class IgnoreNonPythonBackends(FilterTechRequirementsBase):
    filtered_requirements = {"kotlin", "go", "java"}


class IgnoreAIOffers(FilterTechRequirementsBase):
    filtered_requirements = {"ai"}

    @classmethod
    def filter_offer(cls, offer: JobOffer) -> bool:
        has_restricted_requirement = not super().filter_offer(offer)
        if has_restricted_requirement:
            return False

        title = offer.title.lower()

        if "ai" in title or "machine learning" in title:
            logger.debug(f"IgnoreAIOffers skipped: {offer.title}")
            return False

        return True
