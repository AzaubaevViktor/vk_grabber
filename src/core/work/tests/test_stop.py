import asyncio
from time import time

import pytest

from core import BaseWork


pytestmark = pytest.mark.asyncio


class TWork(BaseWork):
    def __init__(self):
        super().__init__()
        self.start = time()
        self.work_time = None

    async def input(self):
        yield time()

    async def process(self, item):
        yield item - self.start

    async def update(self, result):
        self.work_time = result


async def test_stop():
    work = TWork()

    async def work_stop(work_):
        await asyncio.sleep(1)
        work_.need_stop = True

    await asyncio.gather(work_stop(work), work())

    assert work.work_time is not None
    assert work.work_time > 0
