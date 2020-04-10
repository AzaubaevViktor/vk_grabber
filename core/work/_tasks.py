import asyncio
from typing import List, Dict, Any

from core import Log


class _Tasks:
    def __init__(self):
        self.log = Log(self.__class__.__name__)

    async def remove_tasks(self, tasks: Dict[asyncio.Task, Any]):
        assert isinstance(tasks, dict)

        finished = tuple(task for task in tasks.keys() if task.done())
        for task in finished:
            if task.cancelled():
                self.log.warning("Task was cancelled: ", task=task)
            else:
                try:
                    result = await task
                    if result:
                        self.log.important("Task say:", task=task, result=result)
                except Exception:
                    self.log.exception("Task shout:", task=task)

            del tasks[task]

        return tasks
