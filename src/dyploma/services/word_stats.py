import asyncio
from time import time

from app import BaseWorkApp
from core import Attribute
from core.monitor import ListPage, DictPage, PageAttribute
from dyploma.models import Word


class WordPage(DictPage):
    max_value = PageAttribute()
    avg_value = PageAttribute()
    count = PageAttribute()
    datetimes = Attribute(default=None)


class WordsList(ListPage):
    MAX_SIZE = 20
    pass


words_page = WordsList('one_words', "Words")


class WordsUpdater(BaseWorkApp):
    CYCLE_SLEEP_S = 10

    async def main_cycle(self):
        while not self.need_stop:
            word_names = await self._do_aggregate()

            await self._update_pages(word_names)

            start_sleep_time = time()
            while (dt := time() - start_sleep_time) < self.CYCLE_SLEEP_S:
                self.state = f"💤 sleep {self.CYCLE_SLEEP_S - dt:.1f}s"
                if self.need_stop:
                    break
                await asyncio.sleep(min(1, (self.CYCLE_SLEEP_S - dt) / 2))

    async def _do_aggregate(self):
        MotorWordDB_ = self.db.get_collection(Word)
        pipeline = [{"$group": {"_id": "$word", "number": {"$sum": 1}}},
                    {"$sort": {"number": -1}},
                    {"$limit": WordsList.MAX_SIZE}]

        self.state = "Run aggregation"
        word_names = {}
        async for doc in MotorWordDB_.aggregate(pipeline):
            word_names[doc['_id']] = doc['number']
        return word_names

    async def _update_pages(self, word_names):
        self.state = "Create page"

        for word_name, count in word_names.items():
            if word_name not in words_page:
                words_page.append(WordPage(
                    id=word_name,
                    name=word_name,
                    count=count
                ))
