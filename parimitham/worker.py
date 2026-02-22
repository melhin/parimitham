import logging
import os
from uuid import uuid7

import django
from django.core.management import call_command
from django.tasks import DEFAULT_TASK_BACKEND_ALIAS, DEFAULT_TASK_QUEUE_NAME

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
    from parimitham.core.management.commands.execute_task_from_interpreter_queue import (
        InterpreterWorker,
    )

    logger.info("Starting task execution using Interpreter Queue Worker...")
    worker = InterpreterWorker(
        queue_names=[DEFAULT_TASK_QUEUE_NAME],
        interval=1,
        batch=False,
        backend_name=DEFAULT_TASK_BACKEND_ALIAS,
        startup_delay=True,
        max_tasks=None,
        worker_id=str(uuid7()),
    )
    return worker


def configure_db_worker():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "parimitham.settings")
    django.setup(set_prefix=False)
    # Run migrations first
    migrate()

    from django_tasks_db.management.commands import db_worker

    logger.info("Starting task execution using DB Worker...")

    return db_worker.Worker(
        queue_names=[DEFAULT_TASK_QUEUE_NAME],
        interval=1,
        batch=False,
        backend_name=DEFAULT_TASK_BACKEND_ALIAS,
        startup_delay=True,
        max_tasks=None,
        worker_id=str(uuid7()),
    )
