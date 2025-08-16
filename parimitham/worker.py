import logging
import os

import django
from django.core.management import call_command
from django_tasks import DEFAULT_QUEUE_NAME, DEFAULT_TASK_BACKEND_ALIAS

logger = logging.getLogger(__name__)


def migrate():
    """Run Django migrations"""
    call_command("migrate", interactive=False)


def configure_worker():
    # Import Django setup
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parimitham.settings")
    django.setup(set_prefix=False)
    # Run migrations first
    migrate()
    from parimitham.core.management.commands.execute_task_from_interpreter_queue import InterpreterWorker
    logger.info("Starting task execution...")
    worker = InterpreterWorker(
              queue_names=DEFAULT_QUEUE_NAME.split(","),
        interval=1,
        batch=False,
        backend_name=DEFAULT_TASK_BACKEND_ALIAS,
        startup_delay=True,
    )
    return worker
