from __future__ import annotations

import queue
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Generator, Any


class Queue(queue.Queue):
    def __enter__(self, block=True, timeout=None) -> Any:
        return self.get(block, timeout)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.task_done()

    def __iter__(self) -> Generator[Any, None, None]:
        while not self.empty():
            with self as node:
                yield node
