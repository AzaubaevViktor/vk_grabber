import pytest

from database import Model, ModelAttribute

pytestmark = pytest.mark.asyncio


class OneID(Model):
    a = ModelAttribute(uid=True)
    b = ModelAttribute()
    c = ModelAttribute(default=None)


class TwoID(Model):
    a = ModelAttribute(uid=True)
    b = ModelAttribute(uid=True)
    c = ModelAttribute()
    d = ModelAttribute(default=None)


class ThreeId(Model):
    a = ModelAttribute(uid=True)
    b = ModelAttribute(uid=True)
    c = ModelAttribute(uid=True)
    d = ModelAttribute()


async def test_store_new(db):
    m = OneID(a=1, b=2)
    await db.store(m)
    result_dict = await db.find_one(OneID, {'a': 1})
    assert isinstance(result_dict, OneID)
    assert m == result_dict

    result_kwarg = await db.find_one(OneID, a=1)
    assert isinstance(result_kwarg, OneID)
    assert m == result_kwarg


async def test_store_new_2(db):
    m = TwoID(a=1, b=2, c=3)
    await db.store(m)

    result_dict = await db.find_one(TwoID, {'a': 1, 'b': 2})
    assert isinstance(result_dict, TwoID)
    assert m == result_dict

    result_kwarg = await db.find_one(TwoID, a=1, b=2)
    assert isinstance(result_kwarg, TwoID)
    assert m == result_kwarg


async def test_store_exist_update(db):
    m = OneID(a=1, b=2)
    n = OneID(a=1, c=3)

    await db.store(m)
    await db.store(n)

    result = await db.find_one(OneID, a=1)
    assert result.a == 1
    assert result.b == 2
    assert result.c == 3


async def test_store_exist_update_2(db):
    m = TwoID(a=1, b=2, c=3)
    n = TwoID(a=1, b=2, d=4)

    await db.store(m)
    await db.store(n)

    assert await db.count(TwoID) == 1

    result = await db.find_one(TwoID, a=1)
    assert result.a == 1
    assert result.b == 2
    assert result.c == 3
    assert result.d == 4


async def test_store_exist_rewrite(db):
    m = OneID(a=1, b=2)
    n = OneID(a=1, c=3)

    await db.store(m, rewrite=True)

    result = await db.find_one(OneID, a=1)
    assert result.a == 1
    assert result.b == 2
    assert result.c is None

    await db.store(n, rewrite=True)

    result = await db.find_one(OneID, a=1)
    assert result.a == 1
    assert result.b is None
    assert result.c == 3


async def test_store_exist_rewrite_2(db):
    m = TwoID(a=1, b=2, c=3)
    n = TwoID(a=1, b=2, d=4)

    await db.store(m)

    assert await db.count(TwoID) == 1

    result = await db.find_one(TwoID, a=1)
    assert result.a == 1
    assert result.b == 2
    assert result.c == 3
    assert result.d is None

    await db.store(n)

    assert await db.count(TwoID) == 1

    result = await db.find_one(TwoID, a=1)
    assert result.a == 1
    assert result.b == 2
    assert result.c is None
    assert result.d == 4