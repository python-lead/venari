from abc import abstractmethod


class OfferParserInterface:
    @abstractmethod
    async def parse_offers(self, content: str) -> list[dict]:
        pass
