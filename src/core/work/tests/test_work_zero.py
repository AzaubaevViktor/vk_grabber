import asyncio

import pytest

from core import BaseWork


pytestmark = pytest.mark.asyncio


class ZeroWork(BaseWork):
    INPUT_RETRIES = 0
    WAIT_COEF = 0.1

    def __init__(self):
        super().__init__()
        self.input_was_called = 0

    async def input(self):
        assert not self.input_was_called
        self.input_was_called += 1
        yield 1

    async def process(self, item):
        yield item

    async def update(self, result):
        pass


async def test_zero_work():
    work = ZeroWork()
    await asyncio.wait_for(work(), 2)

    assert work.input_was_called == 1
