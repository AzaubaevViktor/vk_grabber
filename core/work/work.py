import asyncio
from time import time
from typing import List, Dict, Optional

from .tasks import TasksManager

from core import Log
from ..monitor import DictPage, PageAttribute


class TaskInfo:
    def __init__(self, item):
        self.processed_callback = None
        if isinstance(item, tuple):
            self.item, self.processed_callback = item
        else:
            self.item = item

        self.state = "💤 Not running"

    def update(self, new_state):
        self.state = new_state

    def __str__(self):
        return self.state


class Stats(DictPage):
    _start_time: int = PageAttribute(default=0)

    state: str = PageAttribute()

    input_items: int = PageAttribute(default=0)
    processed_items: int = PageAttribute(default=0)
    returned_items: int = PageAttribute(default=0)
    updated_items: int = PageAttribute(default=0)
    finished_items: int = PageAttribute(default=0)

    finished_time: Optional[int] = PageAttribute(default=None)

    @PageAttribute.property
    def speed(self):
        dt = (self.finished_time or time()) - self._start_time

        if dt < 1:
            return 0

        return self.processed_items / dt

    @PageAttribute.property
    def reverse_speed(self):
        speed = self.speed

        if speed < 0.000001:
            return 1

        return 1 / speed


class BaseWork:
    start_time = time()

    MUTE_EXCEPTION = True

    PARALLEL = 10
    INPUT_RETRIES = 0
    WAIT_COEF = 1

    need_stop = False

    work_ids: Dict[str, int] = {}

    def __init__(self):
        work_name = self.__class__.__name__
        self.log = Log(work_name)

        self.log.debug("Register work")
        self.work_ids.setdefault(work_name, -1)
        self.work_ids[work_name] += 1
        work_id = f"{work_name}_{self.work_ids[work_name]}"
        self.log.debug("Work registered", work_id=work_id)

        self.stat = Stats(work_id, work_name)

        self.log.debug("Run task manager")
        self.task_manager = TasksManager(self.PARALLEL)
        self.tasks: List[TaskInfo] = []

        self.state = "Base class initialized"

    @property
    def state(self):
        return self.stat.state

    @state.setter
    def state(self, value):
        self.stat.state = value
        self.log.debug(self.state)

    async def warm_up(self):
        pass

    async def input(self):
        yield
        raise NotImplementedError()

    async def process(self, item):
        yield
        raise NotImplementedError()

    async def update(self, result):
        raise NotImplementedError()

    async def shutdown(self):
        pass

    async def __call__(self):
        self.state = "🔥 Warming up"
        await self.warm_up()
        self.stat._start_time = time()

        try:
            await self.main_cycle()
        except Exception:
            self.log.exception("MAIN CYCLE")
            if not self.MUTE_EXCEPTION:
                raise

        self.stat.finished_time = time()

        self.state = "🛑 Shutdown"
        await self.shutdown()

        self.state = "🏁 Finished"

    async def main_cycle(self):
        self.state = "⌛️ Ready to start"
        await asyncio.gather(
            self._input_cycle(),
            self._result_cycle()
        )

    async def _result_cycle(self):
        while True:
            try:
                result = await asyncio.wait_for(self.task_manager.take(), 1)
            except asyncio.TimeoutError:
                continue

            if isinstance(result, TasksManager.Finish):
                break

            await self.update(result)

            self.stat.updated_items += 1

    async def _input_cycle(self):
        self.stat.retries = 0

        while not self.need_stop:
            self.state = "🔎 Wait for new item"

            async for item in self.input():
                self.stat.input_items += 1
                await self.task_manager.put(self._run_task(
                    TaskInfo(item)
                ))
                self.stat.retries = None

            if self.INPUT_RETRIES == 0:
                # Need to run only one time
                self.need_stop = True
                continue

            if self.stat.retries is None:
                # Item found
                self.stat.retries = 0
                await asyncio.sleep(0)
                continue

            if self.stat.retries >= self.INPUT_RETRIES:
                self.log.warning("Too many retries, i'm done", retries=self.stat.retries)
                self.need_stop = True
                continue

            # Retry logic
            self.stat.retries += 1
            self.state = f"🔎 Wait items, repeat №{self.stat.retries}"
            await asyncio.sleep(self.stat.retries * self.WAIT_COEF)

        await self.task_manager.stop()

    async def _run_task(self, info: TaskInfo):
        self.tasks.append(info)

        info.update("🎬 Task started")

        info.update(f"🛠 Processing")

        async for result in self.process(info.item):
            self.stat.returned_items += 1
            info.update(f"🛠 {repr(result)}")
            yield result
            info.update(f"🛠 Processing")

        self.stat.processed_items += 1
        info.update("✅ Finish processing")

        if info.processed_callback:
            info.update("🤙 Run callback")

            self.log.info("Run processed callback", processed_callback=info.processed_callback)
            await info.processed_callback

        self.stat.finished_items += 1

        info.update("🏁 Task finished")

        self.tasks.remove(info)

    async def take_error(self):
        return await self.task_manager.take_error()
