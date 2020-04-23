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
                except RuntimeError:
                    raise
                except Exception:
                    self.log.exception("Task shout:", task=task)

            del tasks[task]

        return tasks


class TasksManager:
    TIMEOUT = 1

    def __init__(self, max_size: int):
        self.log = Log("TasksManager")
        self.size = max_size

        self._tasks = asyncio.Queue(self.size)

        self._results = asyncio.Queue()

        self.executors = [
            asyncio.create_task(self._executor())
        ]

        self.is_run = True

    async def _executor(self):
        self.log.debug("Executor started")
        while self.is_run:
            try:
                coro = await asyncio.wait_for(self._tasks.get(), self.TIMEOUT)
            except asyncio.TimeoutError:
                self.log.debug("No tasks, wait")
                continue

            # TODO: Check task

            self.log.info("New task", task=coro)
            async for result in coro:
                self.log.info("New result", result=result, task=coro)
                await self._results.put(result)

    async def put(self, coro):
        await self._tasks.put(coro)

    async def take(self):
        return await self._results.get()

    async def stop(self):
        self.is_run = False
        for task in self.executors:
            await task

        del self.executors
