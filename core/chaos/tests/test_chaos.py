import asyncio

import pytest


class BaseStore:
    def __init__(self):
        self.items = []

    async def __call__(self, _):
        raise NotImplementedError()


class StoreItem(BaseStore):
    async def __call__(self, item: int):
        self.items.append(item)
        yield item


class StoreItems(BaseStore):
    async def __call__(self, *items: int):
        self.items.extend(items)

        for item in items:
            yield item


async def multiplicator(item: int):
    yield item * 2


class Stats:
    def __init__(self):
        self.count = 0
        self.sum = 0

    async def __call__(self, *items):
        self.count += len(items)
        self.sum += sum(items)


async def adder(item: int):
    yield item + 1


@pytest.mark.parametrize('processor', (
        None,
        multiplicator,
        adder
))
@pytest.mark.parametrize('start', (
        None,
        [1, 2, 3],
        [],
        [x for x in range(10000)]
))
@pytest.mark.parametrize('store_class', (
        StoreItem, StoreItems
))
async def test_item(start, store_class, processor):
    store = store_class()
    chaos = Chaos(start) >> store
    await chaos.run()

    if start is None:
        start = []

    if processor is None:
        async def processor(item: int):
            yield item

    calculated_items = []
    for item in start:
        async for _item in processor(item):
            calculated_items.append(_item)

    assert store.items == calculated_items


@pytest.mark.parametrize('start', (
        [1, 2, 3],
        [],
        [x for x in range(10000)]
))
async def test_combine(start):
    stats = Stats()
    chaos = Chaos(start) >> multiplicator >> adder >> stats

    await chaos.run()

    assert stats.count == 3
    assert stats.sum == sum(x * 2 + 1 for x in start)

