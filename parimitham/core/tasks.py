import logging
import time

from django.tasks import task

logger = logging.getLogger(__name__)


@task()
def cpu_intensive_work_task(sleep_time: int) -> None:
    cpu_intensive_work(sleep_time)


def cpu_intensive_work(sleep_time: int) -> None:
    """
    Mock CPU-intensive work.
    """
    time.sleep(sleep_time)
