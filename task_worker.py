
import asyncio
import logging
import test.support.interpreters.channels as channels
import threading
import time

from rich.logging import RichHandler
from django_app_wsgi import run_worker


# Variables from host interpreter
log_level: int
worker_number: int
channel_id: int

logging.basicConfig(level=log_level, format=f"[{worker_number}] %(message)s", handlers=[RichHandler()])
logger = logging.getLogger(__name__)
shutdown_event = asyncio.Event()
shutdown_event.clear()
recv_channel = channels.RecvChannel(channel_id)


def wait_for_signal():
    while True:
        msg = recv_channel.recv_nowait(default=None)
        if msg == "stop":
            logging.info("Received stop signal, shutting down")
            shutdown_event.set()
        else:
            time.sleep(0.1)

logging.info("Starting task worker")
try:
    thread = threading.Thread(target=wait_for_signal)
    thread.start()
except Exception as e:
    logging.exception(e)

logging.debug("Starting task worker")
try:
    run_worker()
except Exception as e:
    logging.exception(e)
logging.debug("Task worker finished")