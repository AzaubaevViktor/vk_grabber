import pytest

from database import Model, ModelAttribute, DBWrapper


pytestmark = pytest.mark.asyncio


class OneID(Model):
    a = ModelAttribute(uid=True)
    b = ModelAttribute()
    c = ModelAttribute()


async def test_insert(db: DBWrapper):
    obj = OneID(a=1, b=2, c=3)
    await db.insert_many(obj)

    obj = OneID(a=2, b=2, c=3)
    await db.insert_many(obj)

    assert await db.count(OneID) == 2


@pytest.mark.parametrize('variant', (0, 1))
async def test_insert_update(db: DBWrapper, variant):
    obj1 = OneID(a=1, b=2, c=3)
    await db.insert_many(obj1)

    obj2 = await db.find_one(OneID(a=1))

    assert obj1 == obj2

    obj1.b = 3
    obj2.c = 4

    if variant == 0:
        await db.insert_many(obj1, obj2)
    else:
        await db.insert_many(obj1)
        await db.insert_many(obj2)

    assert db.count(OneID) == 1

    result = await db.find_one(OneID(a=1))

    assert result.a == 1
    assert result.b == 3
    assert result.c == 4


async def update_particular(db: DBWrapper):
    obj1 = OneID(a=1, b=2, c=3)
    await db.insert_many(obj1)

    await db.insert_many(OneID(a=1))

    result = await db.find_one(OneID(a=1))

    assert result.a == 1
    assert result.b == 2
    assert result.c == 3
