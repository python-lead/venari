import asyncio
import logging

from venari.engine import Engine
from venari.offer_filters import (
    MinimumWage100,
    IgnoreAIOffers,
    KnownSalary,
    IgnoreFrontendStack,
    IgnoreNonPythonBackends,
)
from vendors.justjoinit.scrapper import JustJoinItScrapper

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(module)s | %(message)s",
    datefmt="%H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)


async def _main_loop() -> None:
    engine = Engine(
        logger=logger, scrapper=JustJoinItScrapper(logger=logger), skip_details=False
    )
    offer_filters = (
        KnownSalary,
        MinimumWage100,
        IgnoreAIOffers,
        IgnoreFrontendStack,
        IgnoreNonPythonBackends,
    )
    engine.add_filters(filters=offer_filters)
    await engine.execute()


def main() -> None:
    logger.info("Hello Venari!")
    try:
        asyncio.run(_main_loop())
    except KeyboardInterrupt:
        logger.warning("Got request to terminate, exiting...")
    finally:
        logger.info("\nExiting venari main!")
