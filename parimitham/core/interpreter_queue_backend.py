import logging
from typing import TypeVar
from uuid import uuid7

from django.tasks import Task, TaskResult, TaskResultStatus
from django.tasks.backends.base import BaseTaskBackend
from typing_extensions import ParamSpec

from queue_bridge import get_shareable_queue

logger = logging.getLogger("__name__")

T = TypeVar("T")
P = ParamSpec("P")


class InterpreterQueueBackend(BaseTaskBackend):
    supports_async_task = True
    supports_get_result = True
    supports_defer = True

    def _task_to_queue(
        self,
        task: Task,
        args: P.args,  # type:ignore[valid-type]
        kwargs: P.kwargs,  # type:ignore[valid-type]
    ) -> TaskResult:
        result = TaskResult(
            id=str(uuid7()),
            task=task,
            args=args,
            kwargs=kwargs,
            status=TaskResultStatus.READY,
            enqueued_at=None,
            started_at=None,
            finished_at=None,
            backend=self.alias,
            last_attempted_at=None,
            errors=[],
            worker_ids=[],
        )
        shareable_task = (task.module_path, args, kwargs)
        worker_queue = get_shareable_queue("worker_queue")
        worker_queue.put(shareable_task)
        logger.info("Task enqueued: %s", result.id)
        return result

    def enqueue(
        self,
        task: Task,
        args: P.args,  # type:ignore[valid-type]
        kwargs: P.kwargs,  # type:ignore[valid-type]
    ) -> None:
        self.validate_task(task)

        self._task_to_queue(task, args, kwargs)
