import asyncio
import logging

from venari.engine import Engine

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)


async def _main_loop() -> None:
    engine = Engine(logger=logger)
    await engine.execute()


def main() -> None:
    logger.info("Hello venari!")
    try:
        asyncio.run(_main_loop())
    except KeyboardInterrupt:
        logger.warning("Got request to terminate, exiting...")
    finally:
        logger.info("Exiting venari main!")
