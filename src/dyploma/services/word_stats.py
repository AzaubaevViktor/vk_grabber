import asyncio
from time import time
from typing import Optional, Dict

import numpy as np

from app import BaseWorkApp
from app.base import AppContext
from core import Attribute, Time
from core.monitor import ListPage, DictPage, PageAttribute
from dyploma.models import Word
from time_series import TimeSeries


def time_info(tm):
    return f"{TimeSeries.fmt_date(tm)} " \
           f"({Time(tm, ago=True)} ago)"


class WordPage(DictPage):
    compares_results: "Compares" = PageAttribute()
    peaks: "PeaksList" = PageAttribute()
    count = PageAttribute()
    ts_stat = PageAttribute()
    max_value = PageAttribute()
    max_moment_raw = Attribute()

    @PageAttribute.property
    def max_moment(self):
        return time_info(self.max_moment_raw)

    mediana = PageAttribute()
    avg_value = PageAttribute()
    ts: TimeSeries = Attribute(default=None)


class WordsList(ListPage):
    MAX_PER_PAGE = 20
    MAX_ITEMS = 100

    def sorted_function(self, item: WordPage):
        return item.count


class Peak(DictPage):
    time_raw = Attribute()

    @PageAttribute.property
    def time(self):
        return time_info(self.time_raw)

    value = PageAttribute()


class PeaksList(ListPage):
    MAX_PER_PAGE = 1

    def sorted_function(self, item: Peak):
        return item.value


class WordsUpdater(BaseWorkApp):
    CYCLE_SLEEP_S = 10
    DOWNLOAD_PERIOD_S = 60 * 60 * 24 * 30 * 6

    MAX_WORK_WINDOW_S = 0.05

    page: WordsList = None
    except_words = ['весь', 'все', 'день',
                    'который', 'свой', 'мой',
                    'так', 'такой', 'если', 'себя',
                    'или', 'очень', 'кто', 'самый', 'тот', 'один']
    need_words = ['поправка', 'конституция', 'путин', 'новый', 'год']

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        assert self.__class__.page is None, "Refactor code"
        self.__class__.page = WordsList('one_words', "Words")
        self.ctx.mon.add_page(self.page)

    async def main_cycle(self):
        while not self.need_stop:
            word_names = await self._do_aggregate()

            await self._update_pages_list(word_names)

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
            name = doc['_id']
            if name in self.except_words:
                continue
            word_names[name] = doc['number']
        for name in self.need_words:
            word_names[name] = await self.db.count(Word, {'word': name})

        return word_names

    async def _update_pages_list(self, word_names):
        self.state = "Create page"

        for word_name, count in word_names.items():
            if word_name not in self.page:
                self.page.append(WordPage(
                    id=word_name,
                    name=word_name,
                    count=count
                ))

    async def _download_word(self, word_name: str, period_s: Optional[int] = None):
        self.state = f"Collecting data for word {word_name}"
        period_s = period_s if period_s is not None else self.DOWNLOAD_PERIOD_S

        word_p = []
        start_time = time() - period_s

        last_update = time()
        async for word in self.ctx.db.find_raw(Word, {'word': word_name}):
            dt = word['date']
            if dt >= start_time:
                word_p.append(dt)

            if time() - last_update > self.MAX_WORK_WINDOW_S:
                await asyncio.sleep(0)
                last_update = time()

        word_ts = np.array(word_p)
        return TimeSeries(word_name, word_ts)

    async def _update_data(self):
        for word_page in self.page.data:  # type: WordPage
            word_page.ts_stat = "Loading"
            ts = await self._download_word(word_page.name)
            word_page.ts_stat = "To grid"
            await asyncio.sleep(0)
            word_page.ts = ts[::60*60*24]
            word_page.ts_stat = "Ready"

    async def _calculate_parameters(self):
        last_update = time()

        for word_page in self.page.data:  # type: WordPage
            if word_page.ts is None:
                continue

            max_moment, max_value = word_page.ts.max()
            word_page.max_value = float(max_value)
            word_page.avg_value = float(word_page.ts.sum() / self.DOWNLOAD_PERIOD_S * 60 * 60 * 24)
            word_page.mediana = word_page.ts.p(50)
            word_page.max_moment_raw = max_moment

            word_page.peaks = PeaksList()

            for tm, value in word_page.ts.peaks():
                peak = Peak(value=value)
                word_page.peaks.append(peak)
                peak.time_raw = tm

            if time() - last_update > self.MAX_WORK_WINDOW_S:
                await asyncio.sleep(0)
                last_update = time()
