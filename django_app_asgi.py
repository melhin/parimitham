import asyncio
import json
import logging
import os
import random
import time
from pathlib import Path
from uuid import uuid4

from django import conf, http, setup, urls
from django.core.handlers.asgi import ASGIHandler
from django.http import StreamingHttpResponse
from django.utils import timezone
from django_tasks import DEFAULT_QUEUE_NAME, DEFAULT_TASK_BACKEND_ALIAS, task

logger = logging.getLogger(__name__)

STREAM_CHECK_INTERVAL = os.environ.get("STREAM_CHECK_INTERVAL", 3)


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent
urlpatterns = []


def configure_settings():
    if not conf.settings.configured:
        conf.settings.configure(
            ALLOWED_HOSTS="*",
            ROOT_URLCONF=__name__,
            INSTALLED_APPS=[
                "django_tasks",
                "django_tasks.backends.database",
            ],
            TASKS={
                "default": {"BACKEND": "django_tasks.backends.database.DatabaseBackend"}
            },
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.sqlite3",
                    "NAME": BASE_DIR / "db.sqlite3",
                    "OPTIONS": {
                        "init_command": (
                            "pragma journal_mode = WAL; pragma synchronous = normal; "
                            "pragma temp_store = memory; pragma mmap_size = 30000000000;"
                        )
                    },
                }
            },
        )


configure_settings()


@task()
def delayed_hi() -> int:
    random_delay = random.randint(1, 5)
    logger.info(f"Sleeping for {random_delay} seconds")
    time.sleep(random_delay)
    logger.info(f"Finished Sleeping for {random_delay} seconds")


async def async_health(request):
    return http.JsonResponse({"status": "ok"})



async def stream_finished(request):
    from django_tasks.backends.database.models import DBTaskResult

    async def streamed_events():
        time_now = timezone.now()
        connection_id = str(uuid4())
        events_count = 0
        while True:
            try:
                result = await DBTaskResult.objects.filter(
                    finished_at__gt=time_now,
                ).afirst()
                if result:
                    dumped_data = json.dumps(
                        {
                            "finished_id": str(result.id),
                            "finished_at": str(result.finished_at),
                            "status": result.status,
                        }
                    )
                    event = "event: new-notification\n"
                    event += f"data: {dumped_data}\n\n"
                    events_count += 1
                    logger.info(f"{connection_id} : Sent events. {events_count}")
                    time_now = result.finished_at
                    yield event
                else:
                    event = "event: heartbeat\n"
                    event += "data: ping\n\n"
                    events_count += 1
                    logger.info(f"{connection_id} Sending heartbeats")
                    yield event

            except asyncio.CancelledError:
                logging.info(
                    f"{connection_id}: Disconnected after events. {events_count}"
                )
                raise
            await asyncio.sleep(STREAM_CHECK_INTERVAL)

    return StreamingHttpResponse(streamed_events(), content_type="text/event-stream")



async def async_root(request):
    await delayed_hi.aenqueue()
    return http.JsonResponse({"message": "Hello World asgi"})

def migrate():
    from django.core.management import call_command

    call_command("migrate", interactive=False)


def configure_worker():
    from django_tasks.backends.database.management.commands.db_worker import (
        Worker,
    )  # noqa

    migrate()
    worker = Worker(
        queue_names=DEFAULT_QUEUE_NAME.split(","),
        interval=1,
        batch=False,
        backend_name=DEFAULT_TASK_BACKEND_ALIAS,
        startup_delay=True,
    )

    return worker


def get_async_urls():
    return [
        urls.path("health/", async_health),
        urls.path("stream/", stream_finished),
        urls.path("", async_root),
    ]


def get_asgi_application():
    global urlpatterns
    setup(set_prefix=False)
    urlpatterns = get_async_urls()
    return ASGIHandler()


app = get_asgi_application()

if __name__ == "__main__":
    import sys

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
