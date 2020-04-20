import asyncio
from time import time
from typing import List, Dict, Type, Any

from ._tasks import _Tasks
from .server import MonitoringServer

from html import escape as html_escape


class Info:
    def __init__(self, item):
        self.item = item
        self.state = "💤 Not running"

    def update(self, new_state):
        self.state = new_state

    def __str__(self):
        return self.state


class Stats:
    def __init__(self, start_time):
        self._start_time = start_time

        self.input_items = 0
        self.processed_items = 0
        self.returned_items = 0

        self.finished_time = None

    @property
    def speed(self):
        dt = (self.finished_time or time()) - self._start_time

        if dt < 1:
            return 0

        return self.processed_items / dt

    @property
    def reverse_speed(self):
        speed = self.speed

        if speed < 0.000001:
            return 1

        return 1 / speed


class BaseWork(_Tasks):
    start_time = time()

    INPUT_REPEATS = 1
    WAIT_COEF = 1

    need_stop = False

    works: List['BaseWork'] = []

    for_monitoring: Dict[str, Any] = {}

    @classmethod
    async def _web_server_gracefull_shutdown(cls, server):
        while True:
            if cls.need_stop:
                break

            # if task.done():
            #     break

            await asyncio.sleep(1)
        await server.shutdown()

    @classmethod
    async def run_monitoring_server(cls, app_info):
        server = MonitoringServer(cls.collect_data, app_info)
        await server()

        asyncio.create_task(cls._web_server_gracefull_shutdown(server))

        # await task

    def __init__(self):
        super().__init__()
        self._state = None
        self.state = "Base class initialized"
        self.tasks: Dict[asyncio.Task, Info] = {}
        self.stat = Stats(self.start_time)

        self.works.append(self)

    @classmethod
    def collect_data(cls):
        result = ""
        result += f"<h3>Workers</h3>"

        for work in cls.works:
            result += f"{work.__class__.__name__}: <br>"
            result += "<ul>"

            result += f"<li>State     : {work.state}</li>"
            result += f"<li>Input     : {work.stat.input_items}</li>"
            result += f"<li>Output    : {work.stat.returned_items}</li>"
            result += f"<li>Processed : {work.stat.processed_items}</li>"
            result += f"<li>Speed     : {work.stat.speed:.2f} items&sol;s </li>"
            result += f"<li>1/Speed   : {work.stat.reverse_speed:.2f} s&sol;items </li>"

            result += "</ul>"

        for name, stat in cls.for_monitoring.items():
            result += f"<h3>{name}</h3>"
            result += "<ul>"

            data = dict(stat)
            key_len = max(len(k) for k in data.keys())

            for k, v in data.items():
                result += f"<li>{k:{key_len}} : {v}</li>"

            result += "</ul>"

        result += "<h3>Tasks:</h3>"
        for work in cls.works:
            result += f"{work.__class__.__name__}: <br>"
            result += "<ul>"

            if not work.tasks:
                result += f"<li>No tasks yet</li>"
            else:
                for task, info in work.tasks.items():
                    result += f"<li>{html_escape(repr(info.item))}: {html_escape(str(info))}</li>"

            result += "</ul>"

        return result

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
        yield
        raise NotImplementedError()

    async def update(self, result):
        raise NotImplementedError()

    async def shutdown(self):
        pass

    async def __call__(self):
        self.state = "🔥 Warming up"
        await self.warm_up()

        try:
            await self.main_cycle()
        except Exception:
            self.log.exception("MAIN CYCLE")

        self.state = "🛑 Shutdown"
        await self.shutdown()
        self.stat.finished_time = time()
        self.state = "🏁 Finished"

    async def main_cycle(self):
        repeats_count = 0
        while True:
            if self.need_stop:
                self.state = "Gracefully shutdown"
                self.log.warning("Gracefully shutdown")
                break

            self.state = "🔎 Wait for new item"

            async for item in self.input():
                self.stat.input_items += 1
                repeats_count = 0

                processed_callback = None
                if isinstance(item, tuple):
                    item, processed_callback = item

                info = Info(item)
                self.tasks[asyncio.create_task(self._run_process(item, info, processed_callback))] = info

            while True:
                self.state = f"🛠 Processing {len(self.tasks)} tasks"

                await self.remove_tasks(self.tasks)

                if not self.tasks:
                    break

                await asyncio.sleep(min(1, self.stat.reverse_speed / 2))

            if repeats_count < self.INPUT_REPEATS:
                repeats_count += 1
                self.state = f"🔎 Wait items, repeat №{repeats_count}"
                await asyncio.sleep(repeats_count * self.WAIT_COEF)
            else:
                self.log.important("No tasks and too many retries, i'm think i'm done")
                break

    async def _run_process(self, item, info: Info, processed_callback=None):
        info.update("🎬 Task started")

        info.update(f"🛠 Processing")

        async for result in self.process(item):
            self.stat.returned_items += 1
            info.update(f"🛠 {repr(result)}")
            await self.update(result)
            info.update(f"🛠 Processing")

        self.stat.processed_items += 1
        info.update("✅ Finish processing")

        if processed_callback:
            info.update("🤙 Run callback")

            self.log.info("Run processed callback", processed_callback=processed_callback)
            await processed_callback

        info.update("🏁 Task finished")
