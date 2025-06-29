
import asyncio
import logging
from concurrent.interpreters import Queue, QueueEmpty
import threading
import time
import signal

from rich.logging import RichHandler
from django_app_wsgi import configure_worker


# Variables from host interpreter
log_level: int
worker_number: int
system_queue: Queue

logging.basicConfig(level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)
shutdown_event = asyncio.Event()
shutdown_event.clear()


def wait_for_signal(worker):
    while True:
        try:
            msg = system_queue.get(timeout=1000)  # Wait for a message from the system queue
        except QueueEmpty:
            continue
        if msg == "stop":
            logging.info(f"Received stop signal - Task - worker {worker_number} shutting down")
            worker.shutdown(signal.SIGINT, None)
        else:
            time.sleep(0.1)

worker = configure_worker()

try:
    thread = threading.Thread(target=wait_for_signal, args=(worker,))
    thread.start()
except Exception as e:
    logging.exception(e)

logging.debug("Starting task worker")

try:
    worker.start()
except Exception as e:
    logging.exception(e)
logging.debug("Task worker finished")