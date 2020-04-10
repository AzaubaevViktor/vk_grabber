import asyncio

import pytest

from core.chaos import Chaos

pytestmark = pytest.mark.asyncio


class BaseStore:
    def __init__(self):
        self.items = []

    async def __call__(self, _):
        raise NotImplementedError()


class StoreItem(BaseStore):
    async def __call__(self, item: int):
        self.items.append(item)
        assert isinstance(item, int) or item is None
        yield item


class StoreItems(BaseStore):
    async def __call__(self, *items: int):
        await asyncio.sleep(0.001)
        self.items.extend(items)

        for item in items:
            assert isinstance(item, int)
            yield item


async def multiplicator(item: int):
    yield item * 2


class Stats:
    def __init__(self):
        self.count = 0
        self.sum = 0

    async def __call__(self, *items):
        await asyncio.sleep(1)
        self.count += len(items)
        self.sum += sum(items)
        yield


async def adder(item: int):
    yield item + 1


@pytest.mark.parametrize('processor', (
        None,
        multiplicator,
        adder
))
@pytest.mark.parametrize('start', (
        [1, 2, 3],
        [],
        [x for x in range(100)]
))
@pytest.mark.parametrize('store_class', (
        StoreItem, StoreItems
))
async def test_item(start, store_class, processor):
    store = store_class()
    chaos = Chaos(start)

    if processor:
        chaos >> processor

    chaos >> store

    await chaos.run()

    if start is None:
        start = [None]

    if processor is None:
        async def processor(item):
            yield item

    calculated_items = []
    for item in start:
        async for _item in processor(item):
            calculated_items.append(_item)

    assert store.items == calculated_items


@pytest.mark.parametrize('start', (
        [1, 2, 3],
        [],
        [x for x in range(100)]
))
async def test_combine(start):
    stats = Stats()
    chaos = Chaos(start) >> multiplicator >> adder >> stats

    await chaos.run()

    assert stats.count == len(start)
    assert stats.sum == sum(x * 2 + 1 for x in start)

