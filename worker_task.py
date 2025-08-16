import logging
import threading
import asyncio
import time
import signal
from socket import socket
from typing import Callable, Optional, Any

from hypercorn.config import Config
from rich.logging import RichHandler
from concurrent.interpreters import Queue, QueueEmpty
from hypercorn.asyncio.run import asyncio_worker
from hypercorn.config import Sockets

from parimitham.worker import configure_worker
from queue_bridge import set_shareable_queue


def shutdown_monitor_task(
    shutdown_queue: Queue,
    worker_number: int,
    shutdown_callback: Callable[[Any], None],
    worker_instance: Optional[Any] = None,
    worker_type: str = "worker"
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
    worker_queue: Queue
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

    def web_worker_shutdown_callback():
        """Callback to handle web worker shutdown."""
        worker_shutdown_event.set()

    logger.info("Starting hypercorn worker")
    try:
        _insecure_sockets = []
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
            args=(shutdown_queue, worker_number, web_worker_shutdown_callback, None, "Web App worker")
        )
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
    worker_queue: Queue
) -> None:
    """
    Task worker task to be executed in a subinterpreter using InterpreterPoolExecutor.
    """
    logging.basicConfig(
        level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()]
    )
    logger = logging.getLogger(__name__)
    logger.info("Starting task worker: %d", worker_number)

    def task_worker_shutdown_callback(worker):
        """Callback to handle task worker shutdown."""
        worker.shutdown(signal.SIGINT, None)

    set_shareable_queue("worker_queue", worker_queue)
    configure_worker()
    logger.info("Task worker configured with queue: %s", worker_queue)

    try:
        # Start signal monitoring thread
        signal_thread = threading.Thread(
            target=shutdown_monitor_task,
            args=(shutdown_queue, worker_number, task_worker_shutdown_callback, worker, "Task worker")
        )
        signal_thread.start()
        
        logging.debug("Starting task worker")
        
    except (OSError, RuntimeError) as e:
        logging.exception("Error in task worker: %s", e)
    finally:
        logging.debug("Task worker finished")
