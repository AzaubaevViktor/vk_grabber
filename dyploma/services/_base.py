from typing import Type, List

from app.base import BaseWorkApp
from database import Model
from dyploma.models import State


class _MetaChooseModelByField(type):
    def __new__(mcs, name, bases: List[type], attrs: dict):
        FIELD_NAME = attrs.get("FIELD_NAME")
        MODEL_CLASS = attrs.get("MODEL_CLASS")

        if FIELD_NAME is None:
            assert FIELD_NAME is None
            FIELD_NAME = name

        attrs['FIELD_NAME'] = FIELD_NAME
        attrs['MODEL_CLASS'] = MODEL_CLASS

        return super(_MetaChooseModelByField, mcs).__new__(mcs, name, bases, attrs)


class _ChooseModelByField(BaseWorkApp, metaclass=_MetaChooseModelByField):
    MODEL_CLASS: Type[Model]
    FIELD_NAME: str
    ADDITIONAL_FILTER: dict = {}

    INPUT_QUERY_LIMIT = 5
    INPUT_RETRIES = 3

    async def warm_up(self):
        assert self.MODEL_CLASS
        assert self.FIELD_NAME

        self.log.info("Cleanup old tasks")

        count = 0
        async for _ in self.db.choose(self.MODEL_CLASS,
                                      {self.FIELD_NAME: State.IN_PROGRESS},
                                      {self.FIELD_NAME: State.NEW}):
            count += 1

        self.log.info("Cleaned old tasks", count=count)

    async def input(self):
        async for item in self.db.choose(self.MODEL_CLASS,
                                         {self.FIELD_NAME: State.NEW, **self.ADDITIONAL_FILTER},
                                         {self.FIELD_NAME: State.IN_PROGRESS},
                                         limit_=self.INPUT_QUERY_LIMIT):
            yield item, self.db.store(item, **{self.FIELD_NAME: State.FINISHED})

    # TODO: Add garbage collector
    # TODO: Add exception handler
