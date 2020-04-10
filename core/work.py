import asyncio
from typing import List

from core import Log


class BaseWork:
    INPUT_REPEATS = 0
    need_stop = False

    def __init__(self):
        self.log = Log(self.__class__.__name__)
        self._state = None
        self.state = "Base class initialized"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self.log.debug(self._state)

    async def warm_up(self):
        pass

    async def input(self):
        yield
        raise NotImplementedError()

    async def process(self, item):
        raise NotImplementedError()

    async def update(self, result):
        raise NotImplementedError()

    async def shutdown(self):
        pass

    async def __call__(self):
        self.state = "Warming up"
        await self.warm_up()

        repeats_count = 0

        tasks: List[asyncio.Task] = []

        while True:
            if self.need_stop:
                self.log.warning("Gracefully shutdown")
                break

            self.state = "Wait for new item"

            async for item in self.input():
                repeats_count = 0
                tasks.append(asyncio.create_task(self._run_process(item)))

            if tasks:
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

            if repeats_count < self.INPUT_REPEATS:
                repeats_count += 1
                self.state = f"Wait items, repeat №{repeats_count}"
                await asyncio.sleep(repeats_count)
            else:
                self.log.important("No tasks and too many retries, i'm think i'm done")
                break

        self.state = "Shutdown"
        await self.shutdown()
        self.state = "Finished"

    async def _run_process(self, item):
        processed_callback = None
        if isinstance(item, tuple):
            item, processed_callback = item

        self.state = f"{type(item)} => ???"
        async for result in self.process(item):
            self.state = f"{type(item)} => {type(result)}"
            await self.update(result)
            self.state = f"{type(item)} => ???"

        if processed_callback:
            self.log.info("Run processed callback", processed_callback=processed_callback)
            await processed_callback

        self.state = "Wait for new item"
