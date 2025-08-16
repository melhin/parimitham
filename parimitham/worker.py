import logging
import os

import django
from django.core.management import call_command

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
    logger.info("Starting task execution...")
    call_command("execute_task_from_interpreter_queue")
