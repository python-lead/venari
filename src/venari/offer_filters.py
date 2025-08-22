from abc import ABC, abstractmethod

from venari.models import JobOffer


class FilterInterface(ABC):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        return True


class IgnoreAIOffers(FilterInterface):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        title = offer.title.lower()

        if "ai" in title or "machine learning" in title:
            return False

        return True


class MinimumWage100(FilterInterface):
    @staticmethod
    def filter_offer(offer: JobOffer) -> bool:
        if offer.salary is None or offer.salary.min < 100:
            return False

        return True
