from typing import Type

from app.base import BaseWorkApp
from database import Model
from dyploma.models import State


class _ChooseModelByField(BaseWorkApp):
    MODEL_CLASS: Type[Model]
    FIELD_NAME: str
    ADDITIONAL_FILTER: dict = {}

    INPUT_QUERY_LIMIT = 5
    INPUT_RETRIES = 3

    async def warm_up(self):
        # TODO: Move into metaclass
        assert self.MODEL_CLASS

        if not hasattr(self, "FIELD_NAME"):
            self.FIELD_NAME = self.__class__.__name__
        # By here

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
