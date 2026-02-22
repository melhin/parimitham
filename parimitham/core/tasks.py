import logging
import random
import time

from django.tasks import task

logger = logging.getLogger(__name__)


@task()
def cpu_intensive_work_task() -> None:
    cpu_intensive_work()


def cpu_intensive_work() -> None:
    """
    Mock CPU-intensive work.
    """
    time.sleep(random.randrange(2, 6))
