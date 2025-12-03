import asyncio
import logging

from connectors.http_clients.httpx_client import HttpxClient
from venari.engine import Engine
from venari.offer_filters import (
    MinimumWage100,
    IgnoreAIOffers,
    KnownSalary,
    IgnoreFrontendStack,
    IgnoreNonPythonBackends,
    IgnoreBigData,
    IgnoreRobotics,
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
    http_client = HttpxClient(logger=logger, max_concurrency=100)
    try:
        await http_client.start()
        engine = Engine(
            logger=logger,
            scrapper=JustJoinItScrapper(client=http_client, logger=logger, max_pages=4),
            skip_details=False,
            order_offers=False,
            open_offers_in_browser=False,
            display_offers=True,
        )
        offer_filters = (
            KnownSalary,
            MinimumWage100,
            IgnoreAIOffers,
            IgnoreFrontendStack,
            IgnoreNonPythonBackends,
            IgnoreBigData,
            IgnoreRobotics,
        )
        engine.add_filters(filters=offer_filters)
        await engine.execute()
    finally:
        logger.info("Venari cleanup in progress.")
        await http_client.terminate()


def main() -> None:
    logger.info("Hello Venari!")
    try:
        asyncio.run(_main_loop())
    except KeyboardInterrupt:
        logger.warning("Got request to terminate, exiting...")
    finally:
        logger.info("Venari shutdown, good luck with the job hunt!")
