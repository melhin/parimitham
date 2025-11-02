"""Bridge module to share queues between subinterpreter workers and Django"""

from concurrent.interpreters import Queue
from functools import cache
from typing import Dict, Optional

# Global storage for worker queues
_worker_queues: Dict[int, Queue] = {}

def set_shareable_queue(name: str, queue: Queue) -> None:
    """Set a shareable queue for the given name"""
    global _worker_queues
    _worker_queues[name] = queue

@cache
def get_shareable_queue(name: str) -> Optional[Queue]:
    """Get the shareable queue for the given name"""
    global _worker_queues
    return _worker_queues.get(name)
