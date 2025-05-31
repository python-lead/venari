import logging
from time import sleep

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s"
)


def main() -> None:
    logger.info("Hello venari!")
    try:
        while True:
            logger.info(".")
            sleep(2)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Exiting venari main!")
