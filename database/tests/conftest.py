import asyncio
from collections import defaultdict
from typing import Dict, List, Type, Union

import pytest
import motor.motor_asyncio

from database import Model


class DBWrapper:
    def __init__(self,
                 client: motor.motor_asyncio.AsyncIOMotorClient,
                 db_name: str):
        self.client = client
        self.db_name = db_name
        self.db = self.client[self.db_name]
        self._collections = {}

    def _get_collection(self, obj: Union[Type[Model], Model]):
        if isinstance(obj, Model):
            klass = obj.__class__
        else:
            klass = obj

        if klass not in self._collections:
            self._collections[klass] = self.db[klass.__name__]

        return self._collections[klass]

    async def insert_many(self, *objs: Model):
        # Divide by classes
        classes: Dict[Type[Model], List[Model]] = defaultdict(list)

        for obj in objs:
            obj.verificate()
            classes[obj.__class__].append(obj)

        tasks = []

        for klass, items in classes.items():
            collection = self._get_collection(klass)
            tasks.append(collection.insert_many([
                item.serialize() for item in items
            ]))

        await asyncio.gather(*tasks)

    async def find(self, obj: Model):
        collection = self._get_collection(obj)
        async for item in collection.find(obj.query()):
            yield type(obj)(**item)

    async def find_one(self, obj: Model):
        collection = self._get_collection(obj)
        item = await collection.find_one(obj.query())
        return type(obj)(**item)

    async def update(self, obj):
        raise NotImplementedError()

    async def delete_all(self, i_understand_delete_all=False):
        assert i_understand_delete_all
        await self.client.drop_database(self.db)


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def client():
    return motor.motor_asyncio.AsyncIOMotorClient('mongodb://root:root@localhost:27017')


@pytest.fixture(scope='function')
async def db(client):
    db = DBWrapper(client, "test")
    yield db
    await db.delete_all(i_understand_delete_all=True)


# @pytest.fixture(scope='session')
# def collection(db):
#     coll = db['test']
#     yield coll
#     coll.delete_many({})
