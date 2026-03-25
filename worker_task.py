import asyncio
import logging
import os
import signal
import threading
import time
from concurrent import interpreters
from concurrent.interpreters import Queue, QueueEmpty
from socket import socket
from typing import Any, Callable, Optional

from hypercorn.asyncio.run import asyncio_worker
from hypercorn.config import Config, Sockets
from rich.logging import RichHandler

from parimitham.worker import configure_db_worker, configure_worker
from queue_bridge import set_shareable_queue

ENABLE_DB_BACKED_TASK = os.getenv("ENABLE_DB_BACKED_TASK", "False").lower() in ("true", "1", "t")


def shutdown_monitor_task(
    shutdown_queue: Queue,
    worker_number: int,
    shutdown_callback: Callable[[Any], None],
    worker_instance: Optional[Any] = None,
    worker_type: str = "worker",
    shutdown_event: Optional[threading.Event] = None,
) -> None:
    """
    Common shutdown monitoring task that waits for shutdown signals.
    """
    while True:
        try:
            msg = shutdown_queue.get(timeout=1.0)
            if msg == "stop":
                logging.info("Received stop signal - %s %d shutting down", worker_type, worker_number)
                if worker_instance:
                    shutdown_callback(worker_instance)
                else:
                    shutdown_callback()
                break
        except QueueEmpty:
            # Check if we should exit via shutdown event
            if shutdown_event and shutdown_event.is_set():
                break
            continue
        except (OSError, RuntimeError):
            # Handle queue operation errors gracefully
            time.sleep(0.1)


def web_worker_task(
    worker_number: int,
    log_level: int,
    application_path: str,
    workers: int,
    bind: str,
    insecure_sockets: tuple,
    shutdown_queue: Queue,
    worker_queue: Queue,
    parent_shutdown_queue: Optional[Queue] = None,
) -> None:
    """
    Web worker task to be executed in a subinterpreter using InterpreterPoolExecutor.
    """
    logging.basicConfig(level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()])

    logger = logging.getLogger(__name__)
    logger.info("Starting web worker: %d", worker_number)
    worker_shutdown_event = asyncio.Event()
    worker_shutdown_event.clear()
    thread_shutdown_event = threading.Event()
    signal_thread = None

    # In worker_task.py
    def web_worker_shutdown_callback():
        """Callback to handle web worker shutdown."""
        logger.info("Shutdown signal received")
        worker_shutdown_event.set()
        thread_shutdown_event.set()
        # Also put a message in the parent queue if available
        if parent_shutdown_queue:
            parent_shutdown_queue.put("shutdown")

    logger.info("Starting hypercorn worker")
    _insecure_sockets = []
    try:
        # Rehydrate the sockets list from the tuple
        for sock_data in insecure_sockets:
            _insecure_sockets.append(socket(*sock_data))
        worker_hypercorn_sockets = Sockets([], _insecure_sockets, [])
        set_shareable_queue("worker_queue", worker_queue)
        worker_config = Config()
        worker_config.application_path = application_path
        worker_config.workers = workers
        worker_config.debug = log_level == logging.DEBUG
        worker_config.accesslog = logger
        worker_config.bind = bind

        # Start signal monitoring thread
        signal_thread = threading.Thread(
            target=shutdown_monitor_task,
            args=(
                shutdown_queue,
                worker_number,
                web_worker_shutdown_callback,
                None,
                "Web App worker",
                thread_shutdown_event,
            ),
        )
        signal_thread.start()

        logger.debug("Starting asyncio worker")
        asyncio_worker(worker_config, worker_hypercorn_sockets, shutdown_event=worker_shutdown_event)

    except (OSError, RuntimeError) as e:
        logger.exception("Error in web worker: %s", e)
        if parent_shutdown_queue:
            try:
                parent_shutdown_queue.put("shutdown")
            except Exception:
                pass
    except Exception as e:
        logger.exception("Unexpected error in web worker: %s", e)
        if parent_shutdown_queue:
            parent_shutdown_queue.put("shutdown")
    finally:
        logging.debug("Starting worker cleanup")
        # Signal the shutdown event to unblock asyncio and threads
        worker_shutdown_event.set()
        thread_shutdown_event.set()

        # Wait for signal thread to finish
        if signal_thread and signal_thread.is_alive():
            try:
                signal_thread.join(timeout=2.0)
            except Exception as e:
                logger.debug("Error joining signal thread: %s", e)

        # Close all sockets explicitly
        for sock in _insecure_sockets:
            try:
                sock.close()
            except Exception as e:
                logger.debug("Error closing socket: %s", e)

        # Give some time for asyncio to shut down gracefully
        time.sleep(0.5)

        logging.debug("Worker cleanup complete")


def task_worker_task(
    worker_number: int,
    log_level: int,
    shutdown_queue: Queue,
    worker_queue: Queue,
    parent_shutdown_queue: Optional[Queue] = None,
) -> None:
    """
    Task worker task to be executed in a subinterpreter using InterpreterPoolExecutor.
    """
    logging.basicConfig(level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()])
    logger = logging.getLogger(__name__)
    logger.info("Starting task worker: %d", worker_number)
    thread_shutdown_event = threading.Event()
    signal_thread = None

    def task_worker_shutdown_callback(worker):
        """Callback to handle task worker shutdown."""
        worker.shutdown(signal.SIGINT, None)
        thread_shutdown_event.set()

    try:
        set_shareable_queue("worker_queue", worker_queue)

        if ENABLE_DB_BACKED_TASK:
            worker = configure_db_worker()
        else:
            worker = configure_worker()
        logger.info("Task worker configured with queue: %s", worker_queue)
        # Start signal monitoring thread
        signal_thread = threading.Thread(
            target=shutdown_monitor_task,
            args=(
                shutdown_queue,
                worker_number,
                task_worker_shutdown_callback,
                worker,
                "Task worker",
                thread_shutdown_event,
            ),
        )
        signal_thread.start()

        worker.run()

    except (OSError, RuntimeError) as e:
        logging.exception("Error in task worker: %s", e)
    except Exception as exc:
        logging.exception(f"Task worker errored: {exc}")
        if parent_shutdown_queue:
            parent_shutdown_queue.put("shutdown")
    finally:
        logging.info("Task worker finished")

        # Signal thread shutdown and wait for it to finish
        thread_shutdown_event.set()
        if signal_thread and signal_thread.is_alive():
            try:
                signal_thread.join(timeout=2.0)
            except Exception as e:
                logging.debug("Error joining signal thread: %s", e)
