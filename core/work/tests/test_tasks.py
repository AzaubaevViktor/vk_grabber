import asyncio

import pytest

from core import Log
from core.work import TasksManager

pytestmark = pytest.mark.asyncio


class TestTasksManager:
    log = Log("test")

    async def task_mid(self, tm, repeats_count):
        self.tasks_count += 1
        await asyncio.sleep(tm / 2)
        for _ in range(repeats_count):
            yield 1
        await asyncio.sleep(tm / 2)
        self.tasks_count -= 1

    async def task_before(self, tm, repeats_count):
        self.tasks_count += 1
        await asyncio.sleep(tm)
        for _ in range(repeats_count):
            yield 1
        self.tasks_count -= 1

    async def task_after(self, tm, repeats_count):
        self.tasks_count += 1
        for _ in range(repeats_count):
            yield 1
        await asyncio.sleep(tm)
        self.tasks_count -= 1

    @pytest.mark.parametrize('max_tasks', [
        1, 2, 10
    ])
    @pytest.mark.parametrize('sleep_time', [
        0.1, 0.01
    ])
    @pytest.mark.parametrize('check_coef', [
        1, 10, 100
    ])
    @pytest.mark.parametrize('real_tasks_coef', [
        1, 2, 10
    ])
    @pytest.mark.parametrize('task_type_name', [
        "task_after", "task_before", "task_mid"
    ])
    async def test_tasks_maxsize(self, max_tasks, sleep_time, check_coef, real_tasks_coef, task_type_name):
        task_type = getattr(self, task_type_name)
        self.tasks_manager = TasksManager(max_tasks)

        self.tasks_count = 0
        self.result = 0

        real_tasks_count = max_tasks * real_tasks_coef
        await asyncio.gather(
            self.put_tasks(real_tasks_count, sleep_time, task_type, check_coef),
            self.take_tasks()
        )

        await self.tasks_manager.stop()

        assert self.result == real_tasks_count * check_coef

    async def put_tasks(self, count, tm, task_type, repeats_count):
        self.log.info("Put tasks to task_manager", count=count, tm=tm, task_type=task_type)
        for _ in range(count):
            self.log.info("New task", task=task_type, tm=tm)
            await self.tasks_manager.put(task_type(tm, repeats_count))

    async def take_tasks(self):
        self.log.info("Wait result from task manager")
        while True:
            try:
                result = await asyncio.wait_for(self.tasks_manager.take(), 1)
            except asyncio.TimeoutError:
                break

            self.log.info("TaskManager get result", result=result)
            self.result += result



