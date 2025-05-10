import logging
import os
import threading
from socket import dup
from time import sleep, time

import _interpreters as interpreters
import test.support.interpreters.channels as channels
from hypercorn.config import Config
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO, format="[main] %(message)s", handlers=[RichHandler()]
)
logger = logging.getLogger(__name__)


WORKERS = os.cpu_count() or 2

"""
    This function is started inside the subinterpreter.
    Running the application:
    python run_dj.py -w 2  -v
"""


class SubinterpreterWorker(threading.Thread):
    def __init__(
        self,
        number: int,
        log_level: int = logging.DEBUG,
    ):
        self.worker_number = number
        self.interp = interpreters.create()
        self.recv_channel, self.send_channel = channels.create()
        self.log_level = log_level
        super().__init__(target=self.run, daemon=True)

    def is_alive(self) -> bool:
        return interpreters.is_running(self.interp) and super().is_alive()

    def request_stop(self):
        logger.info(
            "Sending stop signal to worker {}, interpreter {}".format(
                self.worker_number, self.interp
            )
        )
        self.send_channel.send_nowait("stop")

    def stop(self, timeout: float = 5.0):
        if self.is_alive():
            # wait to stop
            start = time()
            while self.is_alive():
                if time() - start > timeout:
                    logger.warning(
                        "Worker {}, interpreter {} did not stop in time".format(
                            self.worker_number, self.interp
                        )
                    )
                    break
                sleep(0.1)
        else:
            logger.debug(
                "Worker {}, interpreter {} already stopped".format(
                    self.worker_number, self.interp
                )
            )

    def destroy(self):
        if interpreters.is_running(self.interp):
            raise ValueError("Cannot destroy a running interpreter")
        interpreters.destroy(self.interp)


class WebSubinterpreterWorker(SubinterpreterWorker):
    def __init__(
        self,
        application_path: str,
        workers: int,
        enable_async: bool = False,
        bind: str = "127.0.0.1:8000",
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.application_path = application_path
        self.workers = workers
        self.enable_async = enable_async
        self.bind = bind
        self.worker_init = open("web_worker.py", "r").read()

    def run(self):
        # Convert insecure sockets to a tuple of tuples because the Sockets type cannot be shared
        config = Config()
        config.bind = self.bind
        config.workers = self.workers
        sockets = config.create_sockets()
        insecure_sockets = [
            (int(s.family), int(s.type), s.proto, dup(s.fileno()))
            for s in sockets.insecure_sockets
        ]
        logger.debug(
            "Starting worker {}, interpreter {}, enable_async {}, bind {}".format(
                self.worker_number, self.interp, self.enable_async, self.bind
            )
        )
        interpreters.run_string(
            self.interp,
            self.worker_init,
            shared={
                "application_path": self.application_path,
                "worker_number": self.worker_number,
                "insecure_sockets": tuple(insecure_sockets),
                "workers": self.workers,
                "channel_id": self.send_channel.id,
                "log_level": self.log_level,
                "enable_async": self.enable_async,
                "bind": self.bind,
            },
        )
        logger.debug(
            "Worker {}, interpreter {} finished".format(self.worker_number, self.interp)
        )


class TaskSubinterpreterWorker(SubinterpreterWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.worker_init = open("task_worker.py", "r").read()

    def run(self):
        logger.debug(
            "Starting worker {}, interpreter {}".format(self.worker_number, self.interp)
        )
        interpreters.run_string(
            self.interp,
            self.worker_init,
            shared={
                "log_level": self.log_level,
                "worker_number": self.worker_number,
                "channel_id": self.send_channel.id,
            },
        )
        logger.debug(
            "Worker {}, interpreter {} finished".format(self.worker_number, self.interp)
        )


def fill_web_pool(threads, application_path, min_workers):
    t = WebSubinterpreterWorker(
        number=1,
        application_path=application_path,
        workers=min_workers,
        log_level=logger.level,
        bind="127.0.0.1:9001",
    )
    t.start()
    threads.append(t)


def fill_async_pool(threads, application_path, min_workers):
    t = WebSubinterpreterWorker(
        number=2,
        application_path=application_path,
        workers=min_workers,
        log_level=logger.level,
        enable_async=True,
        bind="127.0.0.1:9002",
    )
    t.start()
    threads.append(t)


def fill_task_pool(threads, min_workers):
    for i in range(min_workers):
        t = TaskSubinterpreterWorker(number=i + 2, log_level=logger.level)
        t.start()
        threads.append(t)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-w",
        "--workers",
        dest="workers",
        help="The number of workers to spawn and use, defaults to the number of CPUs",
        default=WORKERS,
        type=int,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="Increase logging verbosity",
        action="store_true",
    )
    args = parser.parse_args()
    sync_application_path = "django_app_wsgi:sync_app"
    async_application_path = "django_app_wsgi:async_app"

    if args.verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    logger.debug("Starting %s workers", args.workers)

    threads: list[SubinterpreterWorker] = []
    fill_async_pool(threads, async_application_path, args.workers)
    fill_web_pool(threads, sync_application_path, args.workers)
    fill_task_pool(threads, args.workers)

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        logger.debug("Received keyboard interrupt, shutting down workers")
        for t in threads:
            t.request_stop()
        for t in threads:
            t.stop()
            # t.destroy()

    # Todo: destroy interpreters on recycle/reload
    # Bug: raises error about remaining sub interpreters after shutdown.
