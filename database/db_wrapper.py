from collections import defaultdict
from typing import Union, Type, Dict, List

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
        elif issubclass(obj, Model):
            klass = obj
        else:
            raise NotImplementedError(f"For {obj}")

        if klass not in self._collections:
            self._collections[klass] = self.db[klass.__name__]

        return self._collections[klass]

    async def insert_many(self, *objs: Model):
        # Divide by classes
        classes: Dict[Type[Model], List[Model]] = defaultdict(list)

        for obj in objs:
            obj.verificate()
            classes[obj.__class__].append(obj)

        for klass, items in classes.items():
            # TODO: Make tasks
            collection = self._get_collection(klass)

            results = await collection.insert_many([
                item.serialize() for item in items
            ])

            for obj, _id in zip(items, results.inserted_ids):
                obj._id = _id

    def _transform(self, obj, item_raw):
        item = type(obj)(**item_raw)
        item.drop_updates()
        return item

    async def find(self, obj: Model):
        collection = self._get_collection(obj)
        async for item_raw in collection.find(obj.query()):
            yield self._transform(obj, item_raw)

    async def find_one(self, obj: Model):
        collection = self._get_collection(obj)
        item_raw = await collection.find_one(obj.query())
        return self._transform(obj, item_raw)

    async def update(self, obj: Model):
        collection = self._get_collection(obj)

        assert obj._id is not None
        updates = obj.updates()
        assert updates

        await collection.update_one(
            {'_id': obj._id},
            {'$set': updates}
        )

        obj.drop_updates()

    async def delete_all(self, i_understand_delete_all=False):
        assert i_understand_delete_all
        await self.client.drop_database(self.db)