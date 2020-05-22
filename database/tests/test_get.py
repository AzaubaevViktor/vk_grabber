import asyncio
from collections import defaultdict

import pytest

from core import Log
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


async def test_none_count(db):
    count = 0
    async for item in db.choose(M, {FIELD_NAME: None}, {FIELD_NAME: True}):
        count += 1

    assert count == ONE_TYPE_COUNT


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


async def test_choose(db):
    async for item_raw in db.choose_raw(M, {FIELD_NAME: False}, {FIELD_NAME: True}):
        assert item_raw[FIELD_NAME] is True

    assert await db.count(M, {FIELD_NAME: True}) == ONE_TYPE_COUNT * 2

    async for item_raw in db.choose_raw(M, {FIELD_NAME: None}, {FIELD_NAME: False}):
        assert item_raw[FIELD_NAME] is False

    assert await db.count(M, {FIELD_NAME: False}) == ONE_TYPE_COUNT

    assert await db.count(M, {FIELD_NAME: None}) == 0


@pytest.mark.parametrize('limit_dividor, limit', (
        (1, None),
        (2, None),
        (3, None),
        (5, None),
        (None, 1),
        (None, 2),
        (None, 3),
))
async def test_choose_limit(db, limit_dividor, limit):
    if limit is not None and limit_dividor is not None:
        pytest.skip()

    if limit is None and limit_dividor is None:
        pytest.skip()

    limit = limit or ONE_TYPE_COUNT // limit_dividor

    count = 0

    async for item_raw in db.choose_raw(M, {FIELD_NAME: False}, {FIELD_NAME: True}, limit_=limit):
        count += 1
        assert item_raw[FIELD_NAME] is True

    assert limit == count

    assert await db.count(M, {FIELD_NAME: True}) == ONE_TYPE_COUNT + limit


@pytest.mark.parametrize('limit', (1, 2, 5))
@pytest.mark.parametrize('sleep_time', (0.05, ))
@pytest.mark.parametrize('retries_', (2, ))
@pytest.mark.parametrize('sleep_coef', (10, ))
@pytest.mark.parametrize('workers_coef', (0.5, 1, 1.5, 3, 3.5))
async def test_parallel(db, limit, sleep_coef, sleep_time, retries_, workers_coef):
    processed = defaultdict(int)

    def gen_func(from_, to_, ):
        async def x(index):
            log = Log(f"{from_}=>{to_}#{index}")

            retries = retries_

            while True:
                found = False

                async for item in db.choose(M, {FIELD_NAME: from_}, {FIELD_NAME: to_}, limit_=limit):
                    log.info(item=item)
                    processed[(from_, to_)] += 1
                    await asyncio.sleep(sleep_time)
                    found = True

                if found:
                    break

                if retries == 0:
                    return

                retries -= 1

                log.warning(retry=retries_ - retries)

                await asyncio.sleep(sleep_time * sleep_coef)
            log.important("STOP")

        return x

    none_false = gen_func(None, False)
    false_true = gen_func(False, True)

    workers_count = int(ONE_TYPE_COUNT * workers_coef)

    if workers_count == 0:
        pytest.skip()

    funcs = []
    funcs += [none_false(_) for _ in range(workers_count)]
    funcs += [false_true(_) for _ in range(workers_count)]

    await asyncio.gather(*funcs)

    assert len(processed) == 2
    assert processed[(None, False)] == min(ONE_TYPE_COUNT, workers_count * limit)
    assert processed[(False, True)] == min(ONE_TYPE_COUNT * 2, workers_count * limit)

    assert await db.count(M, {FIELD_NAME: None}) == max(0, ONE_TYPE_COUNT - workers_count * limit)
    mid_count = ONE_TYPE_COUNT
    if ONE_TYPE_COUNT <= workers_count * limit <= ONE_TYPE_COUNT  * 2:
        mid_count = ONE_TYPE_COUNT * 2 - workers_count * limit
    if ONE_TYPE_COUNT * 2 < workers_count * limit:
        mid_count = 0
    assert await db.count(M, {FIELD_NAME: False}) == mid_count
    assert await db.count(M, {FIELD_NAME: True}) == ONE_TYPE_COUNT + min(ONE_TYPE_COUNT * 2, workers_count * limit)


async def test_sort(db):
    value = -1
    async for item in db.find(M, sort_={'b': 1}):
        assert item.b > value
        value = item.b

    value = ONE_TYPE_COUNT * ONE_TYPE_COUNT * 4
    async for item in db.find(M, sort_={'b': -1}):
        assert item.b < value
        value = item.b

# TODO: Tests for check attributes from kwargs in Model

