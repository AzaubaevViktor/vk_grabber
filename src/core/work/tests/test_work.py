import asyncio
from typing import Sequence

import pytest

from core import BaseWork


pytestmark = pytest.mark.asyncio


class TWork(BaseWork):
    INPUT_RETRIES = 1
    WAIT_COEF = 0.01

    def __init__(self, items: Sequence):
        super().__init__()

        self.items_in = list(items)

        self.items_out = []

    async def input(self):
        if self.items_in:
            yield self.items_in.pop(0)

    async def process(self, item):
        yield item

    async def update(self, result):
        self.items_out.append(result)


@pytest.mark.parametrize('inp', (
    [1, 2, 3, 4],
    [10] * 5,
    [],
    [None, 1, 2, {3: 3}]
))
async def test_simple(inp):
    work = TWork(inp)

    await work()

    assert not work.items_in
    assert work.items_out == inp


@pytest.mark.parametrize('inp', (
    [1, 2, 3, 4, 5, 6, 7],
    [10] * 10
))
@pytest.mark.parametrize('tasks_count', (
    1, 5, 100, 300
))
async def test_many_tasks(inp, tasks_count):
    works = [TWork(inp) for _ in range(tasks_count)]

    await asyncio.gather(*(work() for work in works))

    for work in works:
        assert work.items_out == inp
