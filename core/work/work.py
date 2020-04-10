import asyncio
from time import time
from typing import List, Dict, Type

from ._tasks import _Tasks
from .server import MonitoringServer


class Info:
    def __init__(self, item):
        self.item = item
        self.state = "Not running"

    def update(self, new_state):
        self.state = new_state

    def __str__(self):
        return self.state


class BaseWork(_Tasks):
    start_time = time()

    INPUT_REPEATS = 1
    need_stop = False

    works: List['BaseWork'] = []

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
    async def run_monitoring_server(cls):
        server = MonitoringServer(cls.collect_data)
        await server()

        asyncio.create_task(cls._web_server_gracefull_shutdown(server))

        # await task

    def __init__(self):
        super().__init__()
        self._state = None
        self.state = "Base class initialized"
        self.tasks: Dict[asyncio.Task, Info] = {}

        self.works.append(self)

    @classmethod
    def collect_data(cls):
        from html import escape as html_escape

        result = ""
        for work in cls.works:
            result += f"{work.__class__.__name__}: {work.state} <br>"
            result += "<ul>"
            if not work.tasks:
                result += f"<li>No tasks yet</li>"
            else:
                for task, info in work.tasks.items():
                    result += f"<li>{html_escape(str(info.item))}: {html_escape(str(info))}</li>"
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
        self.state = "Warming up"
        await self.warm_up()

        repeats_count = 0

        while True:
            if self.need_stop:
                self.state = "Gracefully shutdown"
                self.log.warning("Gracefully shutdown")
                break

            self.state = "Wait for new item"

            async for item in self.input():
                repeats_count = 0
                info = Info(item)
                self.tasks[asyncio.create_task(self._run_process(item, info))] = info

            while True:
                self.state = f"Processing {len(self.tasks)} tasks"

                await self.remove_tasks(self.tasks)

                if not self.tasks:
                    break

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

    async def _run_process(self, item, info: Info):
        info.update("Task started")
        processed_callback = None

        if isinstance(item, tuple):
            item, processed_callback = item

        info.update(f"=> ...")

        async for result in self.process(item):
            info.update(f"=> {result}")
            await self.update(result)
            info.update(f"=> ...")

        info.update("Finish processing")

        if processed_callback:
            info.update("Run callback")

            self.log.info("Run processed callback", processed_callback=processed_callback)
            await processed_callback

        info.update("Task finished")
