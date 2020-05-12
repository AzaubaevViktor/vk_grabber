import asyncio
from collections import defaultdict

import pytest

from database import Model, ModelAttribute

pytestmark = pytest.mark.asyncio


FIELD_NAME = 'processed'

# TODO: Create class with parametrize
ONE_TYPE_COUNT = 10


class M(Model):
    a = ModelAttribute(uid=True)
    b = ModelAttribute()


@pytest.fixture(autouse=True, scope='function')
async def create_items(db):
    d = {
        0: None,
        1: False,
        2: True
    }
    for i in range(ONE_TYPE_COUNT * 3):
        additional = {FIELD_NAME: d[i % 3]}

        if additional[FIELD_NAME] is None:
            if i % 2 == 0:
                del additional[FIELD_NAME]

        await db.store(M(a=i, b=i * ONE_TYPE_COUNT), additional)

    for i in range(ONE_TYPE_COUNT * 3):
        assert (await db.find_one_raw(M, a=i)).get(FIELD_NAME, None) == d[i % 3]


async def test_get_find(db):
    async for item in db.find(M, {FIELD_NAME: None}):
        assert item.a % 3 == 0

    async for item in db.find(M, {FIELD_NAME: False}):
        assert item.a % 3 == 1

    async for item in db.find(M, {FIELD_NAME: True}):
        assert item.a % 3 == 2


@pytest.mark.parametrize('limit', (1, 3, 5, 8, 15))
async def test_limit(db, limit):
    count = 0
    async for item in db.find(M, {FIELD_NAME: None}, limit_=limit):
        assert isinstance(item, M)
        count += 1

    assert count == min(limit, ONE_TYPE_COUNT)


async def test_set(db):
    async for item in db.find(M, {FIELD_NAME: False}):
        await db.store(item, {FIELD_NAME: True})

    assert await db.count(M, {FIELD_NAME: True}) == ONE_TYPE_COUNT * 2

    async for item in db.find(M, {FIELD_NAME: None}):
        await db.store(item, {FIELD_NAME: False})

    assert await db.count(M, {FIELD_NAME: False}) == ONE_TYPE_COUNT

    assert await db.count(M, {FIELD_NAME: None}) == 0


@pytest.mark.parametrize('limit', (1, 2, 5))
async def test_parallel(db, limit):
    processed = defaultdict(int)

    def gen_func(from_, to_):
        async def x():
            async for item in db.find(M, {FIELD_NAME: from_}, limit_=limit):
                await db.store(item, {FIELD_NAME: to_})
                processed[(from_, to_)] += 1
                await asyncio.sleep(0.05)
        return x

    none_false = gen_func(None, False)
    false_true = gen_func(False, True)

    funcs = []
    funcs += [none_false() for _ in range(ONE_TYPE_COUNT)]
    funcs += [false_true() for _ in range(ONE_TYPE_COUNT)]

    await asyncio.gather(*funcs)

    assert len(processed) == 2
    assert processed[(None, False)] == ONE_TYPE_COUNT
    assert processed[(False, True)] == ONE_TYPE_COUNT


async def test_sort(db):
    value = -1
    async for item in db.find(M, sort_={'b': 1}):
        assert item.value > value
        value = item.value

    value = ONE_TYPE_COUNT * 4
    async for item in db.find(M, sort_={'b': -1}):
        assert item.value < value
        value = item.value

# TODO: Tests for check attributes from kwargs in Model

