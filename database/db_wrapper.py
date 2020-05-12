from collections import defaultdict
from typing import Union, Type, Dict, List, TypeVar, AsyncIterable, Optional

import motor.motor_asyncio

from core import Log
from database import Model


ModelT = TypeVar("ModelT", Model, Model)
ModelCollectionT = Union[Type[Model], Model]


class DBWrapper:
    def __init__(self,
                 client: motor.motor_asyncio.AsyncIOMotorClient,
                 db_name: str):
        self.log = Log(self.__class__.__name__)
        self.client = client
        self.db_name = db_name
        self.db = self.client[self.db_name]
        self._collections = {}

    def get_collection(self, obj: ModelCollectionT):
        if isinstance(obj, Model):
            klass = obj.__class__
        else:
            klass = obj

        if klass not in self._collections:
            if klass.COLLECTION is not None:
                self._collections[klass] = self.db[klass.COLLECTION]
            else:
                self._collections[klass] = self.db[klass.__name__]

        return self._collections[klass]

    async def store(self, obj: Model, fields: Optional[Dict] = None, rewrite=False):
        collection = self.get_collection(obj)

        id_ = obj._id
        assert id_ is not None

        fields = fields or {}
        fields.update(obj.serialize())

        # TODO: Use args and kwargs for this!
        if not rewrite:
            await collection.update_one(
                {'_id': id_},
                {"$set": fields},
                upsert=True,
            )
        else:
            await collection.replace_one(
                {'_id': id_},
                fields,
                upsert=True,
            )

    async def find_one_raw(self, klass: Type[ModelT], query_: Optional[Dict] = None, **kwargs) -> Optional[ModelT]:
        collection = self.get_collection(klass)

        query_ = query_ or {}
        query = {**query_, **kwargs}

        return await collection.find_one(query)

    async def find_one(self, klass: Type[ModelT], query_: Optional[Dict] = None, **kwargs) -> Optional[ModelT]:
        if item_raw := await self.find_one_raw(klass, query_, **kwargs):
            return self._transform(klass, item_raw)

        return None

    async def find_raw(self, klass: Type[ModelT],
                       query_: Optional[dict] = None,
                       limit_ : Optional[int] = None,
                       sort_: Optional[Dict] = None,
                       **kwargs) -> AsyncIterable[ModelT]:
        # TODO: check attributes from kwargs in Model
        assert not kwargs, NotImplementedError()

        collection = self.get_collection(klass)

        query_ = query_ or {}
        query = {**query_, **kwargs}

        async for raw_item in collection.find(query):
            yield raw_item

    async def find(self, klass: Type[ModelT],
                   query_: Optional[dict] = None,
                   limit_ : Optional[int] = None,
                   sort_: Optional[Dict] = None,
                   **kwargs) -> AsyncIterable[ModelT]:
        async for raw_item in self.find_raw(klass=klass, query_=query_, limit_=limit_, sort_=sort_, **kwargs):
            yield self._transform(klass, raw_item)

    async def count(self, ModelClass: Type[Model], query_: Optional[Dict] = None) -> int:
        assert issubclass(ModelClass, Model)
        collection = self._get_collection(ModelClass)

        query = query_ or {}

        return await collection.count_documents(query)

    # DEPRECATED

    def _get_collection(self, obj: ModelCollectionT):
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
        for item in objs:
            collection = self._get_collection(item)
            collection.update_one({})

        # Divide by classes
        classes: Dict[Type[Model], List[Model]] = defaultdict(list)

        for obj in objs:
            try:
                obj.verificate()
            except ValueError:
                if not force:
                    raise

            classes[obj.__class__].append(obj)

        # TODO: Parallel this please

        for klass, items in classes.items():
            # TODO: Insert with update if exist
            collection = self._get_collection(klass)

            items_insert = []

            for item in items:
                if item._id is not None:
                    if await collection.count_documents({'_id': item._id}, {'limit': 1}):
                        pass

            results = await collection.insert_many([
                {**item.serialize(), **kwargs} for item in items
            ])

            for obj, _id in zip(items, results.inserted_ids):
                obj._id = _id

    def _transform(self, obj: Union[Type[Model], Model], item_raw):
        ModelType = type(obj) if not isinstance(obj, type) else obj
        item = ModelType.soft_create(**item_raw)
        item.drop_updates()
        return item

    async def _find(self, obj: ModelT, limit=None, **kwargs) -> AsyncIterable[ModelT]:
        collection = self._get_collection(obj)
        query = obj.query()
        query.update(kwargs)
        cursor = collection.find(query)
        if limit is not None:
            cursor = cursor.limit(limit)

        async for item_raw in cursor:
            yield self._transform(obj, item_raw)

    async def _find_one(self, obj: Model):
        collection = self._get_collection(obj)
        item_raw = await collection.find_one(obj.query())
        return self._transform(obj, item_raw)

    async def update_model(self, obj: Model, **params):
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

    async def update(self, query: dict, upd: dict, limit=None) -> AsyncIterable[ModelT]:
        Class = query['@model']
        del query['@model']
        collection = self._get_collection(Class)

        # Find ids by query

        # TODO: Get only id's
        cursor = collection.find(query, projection=['_id'])
        if limit is not None:
            cursor = cursor.limit(limit)

        ids = []
        async for item in cursor:
            ids.append(item['_id'])

        # Update by upd
        new_query = {'_id': {'$in': ids}}
        result = await collection.update_many(
            new_query,
            {'$set': upd}
        )

        # Get updated items by id

        async for item_raw in collection.find(new_query):
            yield self._transform(Class, item_raw)

    async def delete_all(self, i_understand_delete_all=False):
        assert i_understand_delete_all
        self.log.important("Delete database", db=self.db)
        await self.client.drop_database(self.db)

    def __str__(self):
        return f"<DBWrapper (mongo): {self.db.name} {self.db}>"
