import pytest

from database import Model, ModelAttribute

pytestmark = pytest.mark.asyncio


class TModel(Model):
    a = ModelAttribute()
    b = ModelAttribute()


async def test_update(db):
    items = [
        TModel(a=x, b=None)
        for x in range(10)
    ]

    await db.insert_many(*items)

    count = 0
    async for obj in db.update({'@model': TModel, 'a': 5}, {'b': 10}):
        count += 1
        assert obj.a == 5
        assert obj.b == 10

    assert count == 1


async def test_update_2(db):
    items = [
        TModel(a=x, b=x // 5)
        for x in range(10)
    ]

    await db.insert_many(*items)

    count = 0
    async for obj in db.update({"@model": TModel, 'b': 1}, {'a': -1}):
        count += 1
        assert obj.a == -1
        assert obj.b == 1

    assert count == 5


@pytest.mark.parametrize('count', (10, 20, 30))
@pytest.mark.parametrize('limit', (1, 2, 4))
async def test_update_get(db, count, limit):
    items = [
        TModel(a=x, b=None)
        for x in range(count)
    ]

    await db.insert_many(*items)

    a_s = []
    async for obj in db.update({'@model': TModel, 'b': None}, {'b': False}, limit=limit):
        assert obj.a is not None
        assert obj.b is False
        a_s.append(obj.a)

    assert len(a_s) == limit

    async for obj in db.update({'@model': TModel, 'b': None}, {'b': False}, limit=limit):
        assert obj.a is not None
        assert obj.b is False
        assert obj.a not in a_s



