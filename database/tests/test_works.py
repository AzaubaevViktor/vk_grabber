import asyncio
from typing import Type

import pytest

from core import BaseWork
from core.work import TasksManager
from database import Model, ModelAttribute

pytestmark = pytest.mark.asyncio


class A(Model):
    number = ModelAttribute()
    processed = ModelAttribute(default=None)


class B(Model):
    id = ModelAttribute(uid=True)
    number10 = ModelAttribute()
    processed = ModelAttribute(default=None)


class C(Model):
    number100 = ModelAttribute()


class BaseTestWork(BaseWork):
    MULTIPLIER = 10
    WAIT_COEF = 0.01

    def __init__(self, db):
        super().__init__()
        self.db = db

    async def _check_exc(self):
        if self.task_manager.has_errors():
            err = await self.take_error()
            if not isinstance(err, TasksManager.Finish):
                e, fmt, _ = err
                print(fmt)
                raise e

    async def _check_models(self, Class: Type[Model]):
        found = False
        async for item in self.db.find(Class()):
            found = True
            assert item.processed is True
        assert found


class AGenerator(BaseTestWork):
    INPUT_RETRIES = 0
    MUTE_EXCEPTION = False

    def __init__(self, db, count):
        super().__init__(db)
        self.orig_count = count

    async def input(self):
        for i in range(self.orig_count):
            yield i

    async def process(self, item: int):
        yield A(number=item)

    async def update(self, result):
        await self.db.insert_many(result)

    async def test(self):
        await self()
        # TODO: Use count
        assert await self.db.count(A) == self.orig_count
        assert self.orig_count == self.stat.input_items
        assert self.orig_count == self.stat.returned_items
        await self._check_exc()


class ABWorker(BaseTestWork):
    INPUT_RETRIES = 5
    MUTE_EXCEPTION = False

    async def input(self):
        async for a in self.db.update({'@model': A, 'processed': None},
                                      {'processed': False},
                                      limit=3):
            yield a, self.db.update_model(a, **{'processed': True})

    async def process(self, a: A):
        for i in range(10):
            yield B(number10=a.number * self.MULTIPLIER + i)

    async def update(self, result: B):
        await self.db.insert_many(result)

    async def test(self):
        await self()
        # TODO: Use count
        assert self.stat.input_items != 0
        assert await self.db.count(B) == self.stat.returned_items
        assert self.stat.input_items * self.MULTIPLIER == self.stat.returned_items
        await self._check_exc()
        await self._check_models(A)


class BCWorker(BaseTestWork):
    INPUT_RETRIES = 5
    MUTE_EXCEPTION = False

    async def input(self):
        async for b in self.db.update({'@model': B, 'processed': None},
                                      {'processed': False},
                                      limit=6):
            yield b, self.db.update_model(b, **{'processed': True})

    async def process(self, b: B):
        for i in range(10):
            yield C(number100=b.number10 * 10 + i)

    async def update(self, result: C):
        await self.db.insert_many(result)

    async def test(self):
        await self()

        assert self.stat.input_items != 0
        assert await self.db.count(C) == self.stat.returned_items
        assert self.stat.input_items * self.MULTIPLIER == self.stat.returned_items
        await self._check_exc()
        await self._check_models(B)


@pytest.mark.parametrize('count', [1, 5, 10])
async def test_linear(db, count):
    gen = AGenerator(db, count)
    await gen.test()

    ab = ABWorker(db)
    await ab.test()

    bc = BCWorker(db)
    await bc.test()


@pytest.mark.parametrize('count', [1, 5, 10])
async def test_parallel(db, count):
    gen = AGenerator(db, count)

    ab = ABWorker(db)

    bc = BCWorker(db)
    await asyncio.gather(
        gen.test(),
        ab.test(),
        bc.test(),
    )
