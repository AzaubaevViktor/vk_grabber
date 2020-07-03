import asyncio
from time import time
from typing import Optional, Dict

import numpy as np

from app import BaseWorkApp
from app.base import AppContext
from core import Attribute
from core.monitor import ListPage, DictPage, PageAttribute
from dyploma.models import Word
from time_series import TimeSeries


class WordPage(DictPage):
    max_value = PageAttribute()
    max_moment = PageAttribute()
    mediana = PageAttribute()
    avg_value = PageAttribute()
    count = PageAttribute()
    peaks: "PeaksList" = PageAttribute()
    compares_results: "Compares" = PageAttribute()
    ts: TimeSeries = Attribute(default=None)


class WordsList(ListPage):
    MAX_PER_PAGE = 20


class PeaksList(ListPage):
    pass


class Peak(DictPage):
    time = PageAttribute()
    value = PageAttribute()


class WordsUpdater(BaseWorkApp):
    CYCLE_SLEEP_S = 10
    DOWNLOAD_PERIOD_S = 60 * 60 * 24 * 30 * 6

    MAX_WORK_WINDOW_S = 0.05

    page: WordsList = None

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        assert self.__class__.page is None, "Refactor code"
        self.__class__.page = WordsList('one_words', "Words")
        self.ctx.mon.add_page(self.page)

    async def main_cycle(self):
        while not self.need_stop:
            word_names = await self._do_aggregate()

            await self._update_pages(word_names)

            await self._update_data()

            await self._calculate_parameters()

            start_sleep_time = time()
            while (dt := time() - start_sleep_time) < self.CYCLE_SLEEP_S:
                self.state = f"💤 sleep {self.CYCLE_SLEEP_S - dt:.1f}s"
                if self.need_stop:
                    break
                await asyncio.sleep(min(1, (self.CYCLE_SLEEP_S - dt) / 2))

    async def _do_aggregate(self) -> Dict[str, int]:
        MotorWordDB_ = self.db.get_collection(Word)
        pipeline = [{"$group": {"_id": "$word", "number": {"$sum": 1}}},
                    {"$sort": {"number": -1}},
                    {"$limit": WordsList.MAX_PER_PAGE}]

        self.state = "Run aggregation"
        word_names = {}
        async for doc in MotorWordDB_.aggregate(pipeline):
            word_names[doc['_id']] = doc['number']
        return word_names

    async def _update_pages(self, word_names):
        self.state = "Create page"

        for word_name, count in word_names.items():
            if word_name not in self.page:
                self.page.append(WordPage(
                    id=word_name,
                    name=word_name,
                    count=count
                ))

    async def _download_word(self, word_name: str, period_s: Optional[int] = None):
        self.state = f"Processing word {word_name}"
        period_s = period_s if period_s is not None else self.DOWNLOAD_PERIOD_S

        word_p = []
        start_time = time() - period_s

        last_update = time()
        async for word in self.ctx.db.find(Word, {'word': word_name}):
            if word.date >= start_time:
                word_p.append(word.date)

            if time() - last_update > self.MAX_WORK_WINDOW_S:
                await asyncio.sleep(0)
                last_update = time()

        word_ts = np.array(word_p)
        return TimeSeries(word_name, word_ts)

    async def _update_data(self):
        for word_page in self.page.data:  # type: WordPage
            ts = await self._download_word(word_page.name)
            word_page.ts = ts[::60*60*24]

    async def _calculate_parameters(self):
        last_update = time()

        for word_page in self.page.data:  # type: WordPage
            max_moment, max_value = word_page.ts.max()
            word_page.max_value = float(max_value)
            word_page.avg_value = float(word_page.ts.sum() / self.DOWNLOAD_PERIOD_S * 60 * 60 * 24)
            word_page.mediana = word_page.ts.p(50)
            word_page.max_moment = TimeSeries.fmt_date(max_moment)

            word_page.peaks = PeaksList()

            for tm, value in word_page.ts.peaks():
                word_page.peaks.append(Peak(time=TimeSeries.fmt_date(tm), value=value))

            if time() - last_update > self.MAX_WORK_WINDOW_S:
                await asyncio.sleep(0)
                last_update = time()
