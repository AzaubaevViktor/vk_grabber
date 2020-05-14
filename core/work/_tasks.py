import asyncio
from traceback import format_exc
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
    class Finish:
        pass

    TIMEOUT = 1

    def __init__(self, max_size: int):
        # TODO: Less logs
        self.log = Log("TasksManager")
        self.size = max_size

        self._tasks = asyncio.Queue(self.size)

        self._results = asyncio.Queue()
        self._exceptions = asyncio.Queue()

        self.is_run = True

        self.executors = [
            asyncio.create_task(self._executor(i)) for i in range(max_size)
        ]

    async def _executor(self, index: int):
        log = self.log['executor'][index]
        log.debug("Executor started")
        while self.is_run:
            try:
                coro = await asyncio.wait_for(self._tasks.get(), self.TIMEOUT)
            except asyncio.TimeoutError:
                continue

            # TODO: Check task
            try:
                async for result in coro:
                    await self._results.put(result)
            except Exception as e:
                log.exception(task=coro)
                await self._exceptions.put((e, format_exc(), coro))

            await asyncio.sleep(0)  #

    async def put(self, coro):
        await self._tasks.put(coro)

    async def take(self):
        return await self._results.get()

    async def take_error(self):
        return await self._exceptions.get()

    def has_errors(self) -> bool:
        return not self._exceptions.empty()

    async def stop(self):
        self.is_run = False
        for task in self.executors:
            await task

        await self._results.put(self.Finish())
        await self._exceptions.put(self.Finish())

        del self.executors
