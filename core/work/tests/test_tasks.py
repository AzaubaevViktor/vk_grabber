import asyncio

import pytest

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('max_tasks', [
    1, 5, 10
])
@pytest.mark.parametrize('sleep_time', [
    0.1, 1, 0.5, 0.01
])
@pytest.mark.parametrize('check_coef', [
    1, 10, 100
])
async def test_tasks_maxsize(max_tasks, sleep_time, check_coef):
    tasks_manager = TasksManager(max_tasks)

    tasks_count = 0

    async def task(tm):
        nonlocal tasks_count
        tasks_count += 1
        await asyncio.sleep(tm)
        tasks_count -= 1


class TestTasksManager:
    async def task_mid(self, tm):
        self.tasks_count += 1
        await asyncio.sleep(tm / 2)
        yield 1
        await asyncio.sleep(tm / 2)
        self.tasks_count -= 1

    async def task_before(self, tm):
        self.tasks_count += 1
        await asyncio.sleep(tm)
        yield 1
        self.tasks_count -= 1

    async def task_after(self, tm):
        self.tasks_count += 1
        yield 1
        await asyncio.sleep(tm)
        self.tasks_count -= 1

    @pytest.mark.parametrize('max_tasks', [
        1, 5, 10
    ])
    @pytest.mark.parametrize('sleep_time', [
        0.1, 1, 0.5, 0.01
    ])
    @pytest.mark.parametrize('check_coef', [
        1, 10, 100
    ])
    @pytest.mark.parametrize('real_tasks_coef', [
        1, 2, 3, 10
    ])
    @pytest.mark.parametrize('task_type', [
        task_after, task_before, task_mid
    ])
    async def test_tasks_maxsize(self, max_tasks, sleep_time, check_coef, real_tasks_coef, task_type):
        self.tasks_manager = TasksManager(max_tasks)

        self.tasks_count = 0
        self.result = 0

        real_tasks_count = max_tasks * real_tasks_coef
        await asyncio.gather(
            self.put_tasks(real_tasks_count, sleep_time, task_type),
            self.take_tasks(),
            self.tasks_manager()
        )

        assert self.result == real_tasks_count

    async def put_tasks(self, count, tm, task_type):
        for _ in range(count):
            await self.tasks_manager.add(task_type(tm))
        await self.tasks_manager.stop()

    async def take_tasks(self):
        while self.tasks_manager.run:
            result = await self.tasks_manager.take()
            self.result += result



