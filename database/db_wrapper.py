from typing import Union, Type, Dict, TypeVar, AsyncIterable, Optional

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

        fields = fields or {}
        fields.update(obj.serialize())

        # TODO: Use args and kwargs for this!
        if (id_ := obj._id) is None:
            await collection.insert_one(
                fields
            )
        else:
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

        cursor = collection.find(query)

        if limit_:
            cursor = cursor.limit(limit_)

        if sort_:
            cursor = cursor.sort(list(sort_.items()))

        async for raw_item in cursor:
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

    async def choose_raw(self, ModelClass: Type[ModelT],
                         query_: Dict,
                         updates_: Dict,
                         limit_: Optional[int] = None,
                         sort_: Optional[int] = None):
        collection = self._get_collection(ModelClass)

        kwargs = {}
        if sort_:
            kwargs['sort'] = list(sort_.items())

        count = 0
        while True:
            raw_item = await collection.find_one_and_update(
                query_,
                {"$set": updates_},
                new=True,
                return_document=True,
                **kwargs
            )

            if raw_item is None:
                return

            yield raw_item

            count += 1
            if (limit_ is not None) and count >= limit_:
                return

    async def choose(self, ModelClass: Type[ModelT],
                     query_: Dict,
                     updates_: Dict,
                     limit_: Optional[int] = None,
                     sort_: Optional[int] = None):
        async for raw_item in self.choose_raw(ModelClass=ModelClass, query_=query_, updates_=updates_, limit_=limit_, sort_=sort_):
            yield self._transform(ModelClass, raw_item)

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

    def _transform(self, obj: Union[Type[Model], Model], item_raw):
        ModelType = type(obj) if not isinstance(obj, type) else obj
        item = ModelType.soft_create(**item_raw)
        item.drop_updates()
        return item

    async def delete_all(self, i_understand_delete_all=False):
        assert i_understand_delete_all
        self.log.important("Delete database", db=self.db)
        await self.client.drop_database(self.db)

    def __str__(self):
        return f"<DBWrapper (mongo): {self.db.name} {self.db}>"
