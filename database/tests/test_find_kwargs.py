import pytest

from database import Model, ModelAttribute


pytestmark = pytest.mark.asyncio


class TParams(Model):
    p = ModelAttribute()


async def test_find_kwargs(db):
    await db.insert_many(*(
        TParams(p=i) for i in range(10)
    ))

    found_items = []

    async for item in db.find(TParams(), limit=5, processed=None):
        assert isinstance(item, TParams)
        assert not item.updates()
        found_items.append(item)

    assert len(found_items) == 5

    for item in found_items:
        item.p = - item.p - 100
        await db.update_model(item, processed=True)

    not_processed_yet = []

    async for item in db.find(TParams(), processed=None):
        assert isinstance(item, TParams)
        assert not item.updates()
        not_processed_yet.append(item)

    assert len(not_processed_yet) == 5

    already_processed = []

    async for item in db.find(TParams(), processed=True):
        assert isinstance(item, TParams)
        assert not item.updates()
        already_processed.append(item)

    assert len(already_processed) == 5

    assert not set(
        item._id for item in not_processed_yet
    ).intersection(set(
        item._id for item in already_processed
    ))
