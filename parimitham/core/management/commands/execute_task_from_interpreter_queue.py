import logging
import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from queue_bridge import get_shareable_queue
from django.utils.module_loading import import_string
from concurrent.interpreters import QueueEmpty
from typing import Any, Tuple

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Poll the subinterpreter queue and execute tasks"

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=float,
            default=1.0,
            help='Queue get timeout in seconds (default: 1.0)'
        )

    def handle(self, *args, **options):
        timeout = options['timeout']

        logger.info("Starting task worker with timeout: %s", timeout)
        worker_queue = get_shareable_queue("worker_queue")
        logger.info("Using worker queue: %s", worker_queue)
        tasks_processed = 0
        
        while True:
            try:
                # Get task from queue with timeout
                shareable_task = worker_queue.get(timeout=timeout)
                
                if shareable_task is None:
                    continue

                logger.info("Got task from queue: %s", shareable_task)
                # Execute the task
                self._execute_task(shareable_task)
                tasks_processed += 1
                
            except QueueEmpty:
                continue
            except (OSError, RuntimeError):
                # Handle queue operation errors gracefully
                time.sleep(0.1)
                        

    def _execute_task(self, shareable_task: Tuple[str, tuple, dict]) -> Any:
        """Execute a task from the shareable task tuple."""
        try:
            module_path, args, kwargs = shareable_task

            logger.info("Starting execution of task: %s", module_path)

            # Import the task function from module path
            task_func = import_string(module_path).func

            # Record start time
            start_time = timezone.now()
            
            # Execute the task
            result = task_func(*args, **kwargs)
            
            # Record completion
            end_time = timezone.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(
                "Task %s completed successfully in %ss", module_path, duration
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Task execution failed for %s: %s", module_path, e,
                exc_info=True
            )