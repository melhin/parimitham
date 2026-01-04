import logging
import random
import time

from django_tasks import task
from unstructured.partition.pdf import partition_pdf

from .models import Document

logger = logging.getLogger(__name__)


@task()
def delayed_hi() -> int:
    random_delay = random.randint(1, 5)
    logger.info(f"Sleeping for {random_delay} seconds")
    time.sleep(random_delay)
    logger.info(f"Finished Sleeping for {random_delay} seconds")
    return random_delay


@task
def process_uploaded_file(document_id: int) -> None:
    logger.info(f"Fetching document with id: {document_id}")
    document = Document.objects.get(id=document_id)
    elements = partition_pdf(file=document.file)
    print(elements)
    logger.info(f"Finished processing document with id: {document_id}")
