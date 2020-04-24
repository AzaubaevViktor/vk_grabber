import asyncio

import pytest

from core import Log, BaseWork
from core.work import TasksManager

pytestmark = pytest.mark.asyncio


class TestError:
    log = Log("test")

    async def error_task(self, x):
        for i in range(x, -1, -1):
            yield 10 / i

    async def test_error(self):
        max_tasks = 5
        tasks_manager = TasksManager(max_tasks)

        # Try to kill every executor
        error_count = max_tasks + 2
        task_value = 10
        for i in range(error_count):
            self.log.info(i)
            await tasks_manager.put(self.error_task(task_value))

        results = []
        while True:
            try:
                results.append(await asyncio.wait_for(tasks_manager.take(), 1))
            except asyncio.TimeoutError:
                break

        assert len(results) == error_count * task_value

        excs = []
        while True:
            try:
                excs.append(await asyncio.wait_for(tasks_manager.take_error(), 1))
            except asyncio.TimeoutError:
                break

        assert len(excs) == error_count

        await tasks_manager.stop()


def test_input_repeats():
    with pytest.raises(DeprecationWarning):
        class X(BaseWork):
            INPUT_REPEATS = 1
