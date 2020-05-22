from app.base import BaseWorkApp
from core import BaseWork
from dyploma.models import Word
from vk_utils import VKPost, VKComment
from word_worker import tokenize


class _LoadModelField(BaseWorkApp):
    MODEL_CLASS = None
    FIELD_NAME = None
    INPUT_QUERY_LIMIT = 5

    async def warm_up(self):
        # Clean field=False
        assert self.MODEL_CLASS
        assert self.FIELD_NAME

        count = 0
        async for _ in self.db.choose(self.MODEL_CLASS, {self.FIELD_NAME: False},
                                      {self.FIELD_NAME: None}):
            count += 1

        self.log.info("Cleanup old tasks", count=count)

    async def input(self):
        async for item in self.db.choose(self.MODEL_CLASS, {self.FIELD_NAME: None},
                                         {self.FIELD_NAME: False},
                                         limit_=self.INPUT_QUERY_LIMIT):
            yield item, self.db.store(item, **{self.FIELD_NAME: True})


class BaseWordKnife(_LoadModelField):
    INPUT_RETRIES = 5
    MODEL_CLASS = None
    FIELD_NAME = 'word_processed'

    async def process(self, post: VKPost):
        for word in tokenize(post.text):
            yield Word(word=word,
                       post_id=post.id,
                       from_id=post.from_id,
                       date=post.date, )

    async def update(self, word: Word):
        await self.db.store(
            word
        )


class WordKnifePost(BaseWordKnife):
    MODEL_CLASS = VKPost


class WordKnifeComment(BaseWordKnife):
    MODEL_CLASS = VKComment


class FoundMaxWords(BaseWork):
    async def input(self):
        pass