import pytest

from database import Model, ModelAttribute

pytestmark = pytest.mark.asyncio


class Check(Model):
    param = ModelAttribute()
    checked: bool = ModelAttribute(default=False)
    x = ModelAttribute(default=None)


async def test_insert_search(db):
    await db.insert_many(*(
        Check(param=i) for i in range(10)
    ))

    uids = []

    async for item in db.find(Check(checked=False)):
        assert isinstance(item, Check)
        assert not item.checked
        uids.append(item.param)

    assert len(set(uids)) == 10


async def test_find(db):
    await db.insert_many(*(
        Check(param=i) for i in range(10)
    ))

    assert db.find_one(Check(param=4)).param == 4


async def test_update_one_time(db):
    items = [Check(param=i, x=i**2) for i in range(10)]
    await db.insert_many(*items)

    items[5].x = -1

    await db.update(items[5])

    item = await db.find_one(Check(param=5))
    assert item.x == -1


async def test_update_many_times(db):
    item = Check(param=10, x=20)

    await db.insert_many(item)

    item2 = await db.find_one(item)

    assert not item2.updates()

    item.x = 100
    item2.param = 100

    await db.update(item)
    await db.update(item2)

    new_item = await db.find_one(item._id)

    assert new_item.x == 100
    assert new_item.param == 100
