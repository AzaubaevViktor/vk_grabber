import asyncio

from core import Log


class _Tasks:
    def __init__(self):
        self.log = Log(self.__class__.__name__)

    async def wait_for_tasks(self, *tasks):
        tasks = list(tasks)

        while tasks:
            finished = tuple(task for task in tasks if task.done())

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

                tasks.remove(task)
            await asyncio.sleep(1)
