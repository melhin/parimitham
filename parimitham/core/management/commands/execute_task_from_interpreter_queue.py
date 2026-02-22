import logging
import signal
import sys
import time
from concurrent.interpreters import QueueEmpty
from types import FrameType
from typing import Any, Tuple

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.module_loading import import_string

from queue_bridge import get_shareable_queue

logger = logging.getLogger(__name__)


class InterpreterWorker:
    def __init__(
        self,
        *,
        queue_names: list[str],
        interval: float,
        batch: bool,
        backend_name: str,
        startup_delay: bool,
        max_tasks: int | None,
        worker_id: str,
    ):
        self.queue_names = queue_names
        self.interval = interval
        self.batch = batch
        self.backend_name = backend_name
        self.startup_delay = startup_delay
        self.max_tasks = max_tasks
        self.worker_id = worker_id
        self.running = True
        self.running_task = False
        self._run_tasks = 0

    def shutdown(self, signum: int, frame: FrameType | None) -> None:
        if not self.running:
            logger.warning("Received %s - terminating current task.", signal.strsignal(signum))
            self.reset_signals()
            sys.exit(1)

        logger.warning(
            "Received %s - shutting down gracefully... (press Ctrl+C again to force)", signal.strsignal(signum)
        )
        self.running = False

        if not self.running_task:
            sys.exit(0)

    def run(self, timeout: float = 1.0) -> None:
        self.running = True
        logger.info("Starting task worker with timeout: %s", timeout)

        worker_queue = get_shareable_queue("worker_queue")
        logger.info("Using worker queue: %s", worker_queue)
        # self.configure_signals()

        while self.running:
            try:
                shareable_task = worker_queue.get(timeout=timeout)

                if shareable_task is None:
                    continue

                logger.info("Got task from queue: %s", shareable_task)
                self.run_task(shareable_task)

            except QueueEmpty:
                continue
            except (OSError, RuntimeError):
                time.sleep(self.interval)

    def run_task(self, shareable_task: Tuple[str, tuple, dict]) -> Any:
        try:
            self.running_task = True
            module_path, args, kwargs = shareable_task

            logger.info("Starting execution of task: %s", module_path)

            task_func = import_string(module_path).func

            start_time = timezone.now()

            result = task_func(*args, **kwargs)

            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()

            logger.info("Task %s completed successfully in %ss", module_path, duration)

            return result

        except Exception as e:
            logger.error("Task execution failed for %s: %s", module_path, e, exc_info=True)
        finally:
            self.running_task = False
            self._run_tasks += 1


class Command(BaseCommand):
    help = "Run an interpreter task worker"

    def add_arguments(self, parser):
        parser.add_argument(
            "--queue-name",
            nargs="?",
            default="default",
            type=str,
            help="The queues to process. Separate multiple with a comma. To process all queues, use '*' (default: %(default)r)",
        )
        parser.add_argument(
            "--interval",
            nargs="?",
            default=0.2,
            type=float,
            help="The interval (in seconds) to wait, when there are no tasks in the queue, before checking for tasks again (default: %(default)r)",
        )
        parser.add_argument(
            "--backend",
            nargs="?",
            default="default",
            type=str,
            dest="backend_name",
            help="The backend to operate on (default: %(default)r)",
        )
        parser.add_argument(
            "--no-startup-delay",
            action="store_false",
            dest="startup_delay",
            help="Don't add a small delay at startup.",
        )
        parser.add_argument(
            "--worker-id",
            nargs="?",
            type=str,
            help="Worker id. MUST be unique across worker pool (default: auto-generate)",
            default="default_worker",
        )

    def handle(self, *args, **options):
        worker = InterpreterWorker(
            queue_names=options["queue_name"].split(","),
            interval=options["interval"],
            batch=options["batch"],
            backend_name=options["backend_name"],
            startup_delay=options["startup_delay"],
            max_tasks=options["max_tasks"],
            worker_id=options["worker_id"],
        )
        worker.run()
