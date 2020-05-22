from vk_utils import VKPost, VKComment
from word_worker import tokenize

from ..models import Word
from ._base import _ChooseModelByField


class BaseWordKnife(_ChooseModelByField):
    INPUT_RETRIES = 5
    MODEL_CLASS = None

    async def process(self, post: VKPost):
        for pos, word in enumerate(tokenize(post.text)):
            yield Word(word=word,
                       post_id=post.id,
                       from_id=post.from_id,
                       date=post.date,
                       position=pos)

    async def update(self, word: Word):
        await self.db.store(
            word
        )


class WordKnifePost(BaseWordKnife):
    MODEL_CLASS = VKPost


class WordKnifeComment(BaseWordKnife):
    MODEL_CLASS = VKComment
