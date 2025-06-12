import asyncio
import logging

from venari.engine import Engine
from venari.offer_filters import MinimumWage100, IgnoreAIOffers

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)


async def _main_loop() -> None:
    engine = Engine(logger=logger)
    offer_filters = (IgnoreAIOffers, MinimumWage100)
    engine.add_filters(filters=offer_filters)
    await engine.execute()


def main() -> None:
    logger.info("Hello venari!")
    try:
        asyncio.run(_main_loop())
    except KeyboardInterrupt:
        logger.warning("Got request to terminate, exiting...")
    finally:
        logger.info("Exiting venari main!")
