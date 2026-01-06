import logging
import math
import time

from django_tasks import task

logger = logging.getLogger(__name__)


@task()
def cpu_intensive_work_task() -> int:
    cpu_intensive_work()


def cpu_intensive_work() -> int:
    """
    Perform simple CPU-intensive work by calculating prime numbers.
    Targets approximately 3-5 seconds of execution time.
    """
    # Set a fixed limit that should take about 3-5 seconds on most modern CPUs
    limit = 300000
    logger.info(f"Starting CPU-intensive prime calculation up to {limit}")

    def is_prime(n: int) -> bool:
        """Check if a number is prime"""
        if n <= 1:
            return False
        if n == 2:
            return True
        if n % 2 == 0:
            return False
        max_divisor = math.isqrt(n) + 1
        for i in range(3, max_divisor, 2):
            if n % i == 0:
                return False
        return True

    prime_count = 0
    start_time = time.time()

    for num in range(2, limit):
        if is_prime(num):
            prime_count += 1

        # Safety check to ensure we don't exceed target time
        if time.time() - start_time > 5:
            logger.info(f"Reached time limit of 5 seconds. Found {prime_count} primes so far")
            break

    execution_time = time.time() - start_time
    logger.info(f"Finished CPU-intensive work. Found {prime_count} primes in {execution_time:.2f} seconds")
    return prime_count
