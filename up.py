"""
InterpreterPoolExecutor-based worker management for Django application.
This replaces the manual subinterpreter management with the new Python 3.14+ InterpreterPoolExecutor.
"""

import logging
import time
from concurrent.futures import Future
from concurrent.futures.interpreter import InterpreterPoolExecutor
from concurrent.interpreters import Queue, QueueEmpty, create_queue
from socket import dup
from typing import List, Optional

from hypercorn.config import Config
from rich.logging import RichHandler

from worker_task import task_worker_task, web_worker_task

logging.basicConfig(level=logging.INFO, format="[pool_manager] %(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)

WEB_WORKERS = 2
TASK_WORKERS = 1


class InterpreterPoolManager:
    """
    Manages worker processes using InterpreterPoolExecutor.
    """

    def __init__(self, max_workers: int = None):
        self.max_workers = max_workers or WEB_WORKERS
        self.futures: List[Future] = []
        self.shutdown_queues = []  # List of Queue objects
        self._shutdown_requested = False
        self._parent_shutdown_queue: Optional[Queue] = None
        self.executor = InterpreterPoolExecutor(max_workers=self.max_workers)

    def set_parent_shutdown_queue(self, queue: Queue):
        """Set the queue for parent communication."""
        self._parent_shutdown_queue = queue

    def start_web_workers(self, app_path: str, workers: int, worker_queue: Queue, bind: str = "127.0.0.1:8000"):
        """Start web workers using the pool executor."""

        logger.info("Starting web workers with InterpreterPoolExecutor")

        # Setup socket configuration
        config = Config()
        config.bind = bind
        config.workers = workers
        sockets = config.create_sockets()

        # Store socket metadata (not the actual duplicated FDs yet)
        socket_metadata = tuple([(int(s.family), int(s.type), s.proto) for s in sockets.insecure_sockets])

        for i in range(workers):
            # Duplicate sockets for EACH worker to avoid sharing file descriptors
            insecure_sockets = tuple(
                [
                    (family, sock_type, proto, dup(s.fileno()))
                    for (family, sock_type, proto), s in zip(socket_metadata, sockets.insecure_sockets)
                ]
            )

            # Submit web worker task
            # Create shutdown queue for each web worker
            shutdown_queue = create_queue()
            self.shutdown_queues.append(shutdown_queue)
            future = self.executor.submit(
                web_worker_task,
                worker_number=i + 1,
                log_level=logger.level,
                application_path=app_path,
                workers=workers,
                bind=bind,
                insecure_sockets=insecure_sockets,
                shutdown_queue=shutdown_queue,
                worker_queue=worker_queue,
                parent_shutdown_queue=self._parent_shutdown_queue,
            )
            self.futures.append(future)

        # Close the original sockets in the parent process after duplication
        for s in sockets.insecure_sockets:
            try:
                s.close()
            except Exception as e:
                logger.warning("Failed to close original socket: %s", e)

        logger.debug("Web workers submitted to pool executor")

    def start_task_workers(self, num_workers: int, worker_queue: Queue):
        """Start task workers using the pool executor."""

        logger.info("Starting %d task workers with InterpreterPoolExecutor", num_workers)

        for i in range(num_workers):
            # Create shutdown queue for each task worker
            shutdown_queue = create_queue()
            self.shutdown_queues.append(shutdown_queue)

            # Submit task worker
            future = self.executor.submit(
                task_worker_task,
                worker_number=i + 1,
                log_level=logger.level,
                shutdown_queue=shutdown_queue,
                worker_queue=worker_queue,
                parent_shutdown_queue=self._parent_shutdown_queue,
            )
            self.futures.append(future)

        logger.debug("Task workers submitted to pool executor")

    def shutdown(self, timeout: float = 5.0):
        """Shutdown all workers gracefully."""
        if self._shutdown_requested:
            return

        self._shutdown_requested = True
        logger.info("Shutting down worker pool...")

        # Send stop signals to all workers
        for queue in self.shutdown_queues:
            try:
                queue.put("stop")
            except Exception as e:
                logger.warning("Failed to send stop signal: %s", e)

        # Wait for futures to complete
        start_time = time.time()
        for future in self.futures:
            remaining_timeout = max(0, timeout - (time.time() - start_time))
            try:
                future.result(timeout=remaining_timeout)
            except Exception as e:
                logger.warning(f"Worker task completed with error: {e}")

        # Shutdown the executor
        if self.executor:
            self.executor.shutdown(wait=True, cancel_futures=True)
            logger.info("Pool executor shutdown complete")

    def join(self):
        """Wait for all workers to complete."""
        for future in self.futures:
            try:
                future.result()
            except Exception as e:
                logger.error("Worker task failed: %s", e)
                raise

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()


class ErrorRaisedFromPoolException(Exception):
    pass


def run_application(
    app_path: str,
    workers: int = WEB_WORKERS,
    bind: str = "127.0.0.1:8000",
    task_workers: int = TASK_WORKERS,
):
    logger.info("Starting Django application and task workers with InterpreterPoolExecutor")
    logger.info("Web workers: %d, Task workers: %d, Bind: %s", workers, task_workers, bind)

    # Create parent shutdown queue
    parent_shutdown_queue = create_queue()

    # Calculate total workers needed
    total_workers = workers + task_workers  # N web workers + M task workers
    worker_queue = create_queue()

    with InterpreterPoolManager(max_workers=total_workers) as pool:
        # Set parent shutdown queue
        pool.set_parent_shutdown_queue(parent_shutdown_queue)

        try:
            # Start workers
            pool.start_web_workers(app_path, workers, worker_queue, bind)
            pool.start_task_workers(task_workers, worker_queue)

            logger.info("All workers started. Press Ctrl+C to stop.")

            # Wait for shutdown signal from parent queue or completion
            while True:
                # Check for shutdown message with a small timeout
                try:
                    message = parent_shutdown_queue.get(timeout=2)
                    if message == "shutdown":
                        logger.info("Received shutdown request from worker")
                        raise ErrorRaisedFromPoolException()
                except QueueEmpty:
                    continue

            # Wait for completion
            pool.join()
        except ErrorRaisedFromPoolException:
            logger.error("Error Raised from pool exception")
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        finally:
            logger.info("Application shutdown complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Django application with InterpreterPoolExecutor")
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        help="The number of web workers to spawn and use",
        default=WEB_WORKERS,
        type=int,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase logging verbosity",
        action="store_true",
        default=True,
    )
    parser.add_argument(
        "-b",
        "--bind",
        help="Bind address for the web server",
        default="0.0.0.0:9001",
        type=str,
    )
    parser.add_argument(
        "-t",
        "--task-workers",
        help="Number of task workers",
        default=TASK_WORKERS,
        type=int,
    )

    args = parser.parse_args()

    # Set up logging
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    application_path = "parimitham.wsgi:application"

    # Run the application
    run_application(
        app_path=application_path,
        workers=args.workers,
        bind=args.bind,
        task_workers=args.task_workers,
    )
