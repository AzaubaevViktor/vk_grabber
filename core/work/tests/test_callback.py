import pytest

from core import BaseWork


pytestmark = pytest.mark.asyncio


class CallbackWork(BaseWork):
    INPUT_RETRIES = 0

    def __init__(self, count):
        super().__init__()
        self.count = count
        self.counter_callback = 0

    async def callback(self):
        self.counter_callback += 1

    async def input(self):
        for i in range(self.count):
            yield i, self.callback()

    async def process(self, item):
        yield item

    async def update(self, result):
        pass


@pytest.mark.parametrize('count', (0, 10))
async def test_callback(count):
    work = CallbackWork(count)
    await work()

    assert work.counter_callback == count
