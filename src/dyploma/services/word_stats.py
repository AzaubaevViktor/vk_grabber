import asyncio
from time import time

from app import BaseWorkApp
from core.monitor import ListPage, DictPage, PageAttribute
from dyploma.models import Word


class WordPage(DictPage):
    max_value = PageAttribute()
    avg_value = PageAttribute()
    count = PageAttribute()


class WordsList(ListPage):
    MAX_SIZE = 20
    pass


words_page = WordsList('one_words', "Words")


class WordsUpdater(BaseWorkApp):
    CYCLE_SLEEP_S = 10

    async def main_cycle(self):
        MotorWordDB_ = self.db.get_collection(Word)
        pipeline = [{"$group": {"_id": "$word", "number": {"$sum": 1}}},
                    {"$sort": {"number": -1}},
                    {"$limit": WordsList.MAX_SIZE}]

        while not self.need_stop:
            self.state = "Run aggregation"
            word_names = []
            async for doc in MotorWordDB_.aggregate(pipeline):
                word_names.append(doc['_id'])

            self.state = "Create page"

            for word_name in word_names:
                words_page.append(WordPage(
                    id=word_name,
                    name=word_name
                ))

            start_sleep_time = time()
            while (dt := time() - start_sleep_time) < self.CYCLE_SLEEP_S:
                self.state = f"💤 sleep {self.CYCLE_SLEEP_S - dt:.1f}s"
                if self.need_stop:
                    break
                await asyncio.sleep(min(1, (self.CYCLE_SLEEP_S - dt) / 2))
