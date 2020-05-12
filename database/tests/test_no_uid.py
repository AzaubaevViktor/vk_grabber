import pytest

from database import Model, ModelAttribute


pytestmark = pytest.mark.asyncio


class A(Model):
    a = ModelAttribute()
    b = ModelAttribute()
    c = ModelAttribute()


@pytest.mark.parametrize('count', (10, 15))
async def test_insert_find(db, count):
    c_true_count = 0
    for i in range(count):
        is_three_mod = i % 3 == 0
        await db.store(A(a=i, b=i*2, c=is_three_mod))
        c_true_count += is_three_mod

    assert (await db.find_one(A, b=2)).a == 1

    async for item in db.find(A):
        assert item.a * 2 == item.b

    processed = 0
    limit = count // 6

    async for item in db.choose(A, {'c': True}, {'c': False}, limit_=limit):
        assert item.c is False
        assert item.a % 3 == 0
        processed += 1

    assert processed == min(limit, count)

    assert await db.count(A) == count
    assert await db.count(A, {'c': True}) == c_true_count - processed
    assert await db.count(A, {'c': False}) == count - (c_true_count - processed)
