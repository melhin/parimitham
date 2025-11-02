import logging
import random
import time

from django_tasks import task

logger = logging.getLogger(__name__)


@task()
def delayed_hi() -> int:
    random_delay = random.randint(1, 5)
    logger.info(f"Sleeping for {random_delay} seconds")
    time.sleep(random_delay)
    logger.info(f"Finished Sleeping for {random_delay} seconds")
    return random_delay
