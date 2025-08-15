import logging
import threading
import asyncio
import time
import signal
from socket import socket

from hypercorn.config import Config
from rich.logging import RichHandler
from concurrent.interpreters import Queue, QueueEmpty
from hypercorn.asyncio.run import asyncio_worker
from hypercorn.config import Sockets

from django_app_wsgi import configure_worker


def web_worker_task(
    worker_number: int,
    log_level: int,
    application_path: str,
    workers: int,
    bind: str,
    insecure_sockets: tuple,
    shutdown_queue: Queue,
) -> None:
    """
    Web worker task to be executed in a subinterpreter using InterpreterPoolExecutor.
    """
    logging.basicConfig(
        level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()]
    )

    logger = logging.getLogger(__name__)
    logger.info("Starting web worker: %d", worker_number)
    worker_shutdown_event = asyncio.Event()
    worker_shutdown_event.clear()

    def wait_for_shutdown_signal():
        """Wait for shutdown signal from the main process."""
        while True:
            try:
                msg = shutdown_queue.get(timeout=1.0)
                if msg == "stop":
                    logging.info("Received stop signal - Web App - worker shutting down")
                    worker_shutdown_event.set()
                    break
            except QueueEmpty:
                continue
            except (OSError, RuntimeError):
                # Handle queue operation errors gracefully
                time.sleep(0.1)

    logger.info("Starting hypercorn worker")
    try:
        _insecure_sockets = []
        # Rehydrate the sockets list from the tuple
        for sock_data in insecure_sockets:
            _insecure_sockets.append(socket(*sock_data))
        worker_hypercorn_sockets = Sockets([], _insecure_sockets, [])

        worker_config = Config()
        worker_config.application_path = application_path
        worker_config.workers = workers
        worker_config.debug = log_level == logging.DEBUG
        worker_config.accesslog = logger
        worker_config.bind = bind
        
        # Start signal monitoring thread
        signal_thread = threading.Thread(target=wait_for_shutdown_signal)
        signal_thread.start()
        
        logger.debug("Starting asyncio worker")
        asyncio_worker(worker_config, worker_hypercorn_sockets, shutdown_event=worker_shutdown_event)
        
    except (OSError, RuntimeError) as e:
        logger.exception("Error in web worker: %s", e)
    finally:
        logging.debug("asyncio worker finished")


def task_worker_task(
    worker_number: int,
    log_level: int,
    shutdown_queue: Queue,
) -> None:
    """
    Task worker task to be executed in a subinterpreter using InterpreterPoolExecutor.
    """
    logging.basicConfig(
        level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()]
    )

    def wait_for_shutdown_signal(worker):
        """Wait for shutdown signal from the main process."""
        while True:
            try:
                msg = shutdown_queue.get(timeout=1.0)
                if msg == "stop":
                    logging.info("Received stop signal - Task worker %d shutting down", worker_number)
                    worker.shutdown(signal.SIGINT, None)
                    break
            except QueueEmpty:
                continue
            except (OSError, RuntimeError):
                # Handle queue operation errors gracefully
                time.sleep(0.1)

    worker = configure_worker()

    try:
        # Start signal monitoring thread
        signal_thread = threading.Thread(target=wait_for_shutdown_signal, args=(worker,))
        signal_thread.start()
        
        logging.debug("Starting task worker")
        worker.start()
        
    except (OSError, RuntimeError) as e:
        logging.exception("Error in task worker: %s", e)
    finally:
        logging.debug("Task worker finished")
