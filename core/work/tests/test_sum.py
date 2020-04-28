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

        self.sum = 0

    async def input(self):
        if self.items_in:
            yield self.items_in.pop(0)

    async def process(self, *items):
        yield sum(items)

    async def update(self, result):
        self.sum += result


@pytest.mark.parametrize('inp', (
    [1, 2, 3, 4, 5],
    [10] * 5
))
async def test_sum(inp):
    work = TWork(inp)

    await work()

    assert work.sum == sum(inp)
