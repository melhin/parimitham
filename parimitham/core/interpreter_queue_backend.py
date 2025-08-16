from dataclasses import dataclass
from typing import TypeVar

from typing_extensions import ParamSpec

from django_tasks.backends.base import BaseTaskBackend
from django_tasks.task import Task
from django_tasks.task import TaskResult as BaseTaskResult, ResultStatus
from uuid import uuid7
from queue_bridge import get_shareable_queue

import logging


logger = logging.getLogger("__name__")

T = TypeVar("T")
P = ParamSpec("P")



@dataclass(frozen=True)
class TaskResult(BaseTaskResult[T]):
    ...


class InterpreterQueueBackend(BaseTaskBackend):
    supports_async_task = True
    supports_get_result = True
    supports_defer = True

    def _task_to_queue(
        self,
        task: Task[P, T],
        args: P.args,  # type:ignore[valid-type]
        kwargs: P.kwargs,  # type:ignore[valid-type]
    ) -> TaskResult:

        result  = TaskResult(
            id=str(uuid7()),
            task=task,
            args=args,
            kwargs=kwargs,
            status=ResultStatus.NEW,
            enqueued_at=None,
            started_at=None,
            finished_at=None,
            backend=self.alias,
        )
        shareable_task = ( task.module_path, args, kwargs)
        worker_queue = get_shareable_queue("worker_queue")
        logger.info("Enqueuing in queue : %s", worker_queue)
        worker_queue.put(shareable_task)
        logger.info("Task enqueued: %s", result.id)
        return result

    def enqueue(
        self,
        task: Task[P, T],
        args: P.args,  # type:ignore[valid-type]
        kwargs: P.kwargs,  # type:ignore[valid-type]
    ) -> TaskResult[T]:
        self.validate_task(task)

        result = self._task_to_queue(task, args, kwargs)

        return result
