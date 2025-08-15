import logging
import os
import random
import time
from pathlib import Path

from django import conf, http, setup, urls
from django.core.handlers.wsgi import WSGIHandler
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


def root(request):
    delayed_hi.enqueue()
    return http.JsonResponse({"message": "Hello World wsgi"})


def health(request):
    return http.JsonResponse({"status": "ok"})


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


def get_sync_urls():
    return [urls.path("health/", health), urls.path("", root)]


def get_wsgi_application():
    global urlpatterns
    setup(set_prefix=False)
    urlpatterns = get_sync_urls()
    return WSGIHandler()

app = get_wsgi_application()

if __name__ == "__main__":
    import sys

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
