from collections import defaultdict
from typing import Union, Type, Dict, List, TypeVar, AsyncIterable

import motor.motor_asyncio

from core import Log
from database import Model


ModelT = TypeVar("ModelT", Model, Model)


class DBWrapper:
    def __init__(self,
                 client: motor.motor_asyncio.AsyncIOMotorClient,
                 db_name: str):
        self.log = Log(self.__class__.__name__)
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

    async def insert_many(self, *objs: Model, force=False, **kwargs):
        # Divide by classes
        classes: Dict[Type[Model], List[Model]] = defaultdict(list)

        for obj in objs:
            try:
                obj.verificate()
            except ValueError:
                if not force:
                    raise
                self.log.exception("It's ok because force write mode")

            classes[obj.__class__].append(obj)

        for klass, items in classes.items():
            # TODO: Make tasks
            collection = self._get_collection(klass)

            results = await collection.insert_many([
                {**item.serialize(), **kwargs} for item in items
            ])

            for obj, _id in zip(items, results.inserted_ids):
                obj._id = _id

    def _transform(self, obj: Model, item_raw):
        item = type(obj).soft_create(**item_raw)
        item.drop_updates()
        return item

    async def find(self, obj: ModelT, limit=None, **kwargs) -> AsyncIterable[ModelT]:
        collection = self._get_collection(obj)
        query = obj.query()
        query.update(kwargs)
        cursor = collection.find(query)
        if limit is not None:
            cursor = cursor.limit(limit)

        async for item_raw in cursor:
            yield self._transform(obj, item_raw)

    async def find_one(self, obj: Model):
        collection = self._get_collection(obj)
        item_raw = await collection.find_one(obj.query())
        return self._transform(obj, item_raw)

    async def update(self, obj: Model, **params):
        collection = self._get_collection(obj)

        assert obj._id is not None
        updates = obj.updates()
        updates.update(params)
        assert updates

        await collection.update_one(
            {'_id': obj._id},
            {'$set': updates}
        )

        obj.drop_updates()

    async def delete_all(self, i_understand_delete_all=False):
        assert i_understand_delete_all
        self.log.important("Delete database", db=self.db)
        await self.client.drop_database(self.db)

    def __str__(self):
        return f"<DBWrapper (mongo): {self.db.name} {self.db}>"
