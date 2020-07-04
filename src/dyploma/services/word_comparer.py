import asyncio
from time import time

from app import BaseWorkApp
from core.monitor import ListPage, PageAttribute, DictPage
from dyploma.services.word_stats import WordsUpdater, WordPage
from time_series import TimeSeries


class ComparesResult(DictPage):
    word = PageAttribute()
    score = PageAttribute()


class Compares(ListPage):
    MAX_PER_PAGE = 5
    SORT_DIRECTION_LARGER_TOP = False

    def sorted_function(self, item: ComparesResult):
        return item.score


class WordsComparer(BaseWorkApp):
    CYCLE_SLEEP_S = 16

    INF = 10 ** 5

    async def formulae(self, word_source: WordPage, word_other: WordPage):
        # Search near last maximums
        if word_source.peaks is None:
            return self.INF
        peak_source = word_source.peaks.from_sorted(0)
        if peak_source is None:
            return self.INF

        if word_other.peaks is None:
            return self.INF
        peak_other = word_other.peaks.from_sorted(0)
        if peak_other is None:
            return self.INF

        return abs(peak_source.time_raw - peak_other.time_raw) / 60 / 60 / 24

    async def main_cycle(self):
        while not self.need_stop:
            # last_update = time()

            for word_source in WordsUpdater.page.data:  # type: WordPage
                if word_source is None:
                    continue
                if word_source.compares_results is None:
                    word_source.compares_results = Compares()

                for word_other in WordsUpdater.page.data:  # type: WordPage
                    if word_other is None:
                        continue

                    if word_other.name == word_source.name:
                        continue

                    score = float(await self.formulae(
                        word_source,
                        word_other
                    ))

                    word_source.compares_results.update(
                        ComparesResult(
                            id=f"{word_source.name}-{word_other.name}",
                            word=word_other.name,
                            score=score
                        ))

            # TODO: To method
            start_sleep_time = time()
            while (dt := time() - start_sleep_time) < self.CYCLE_SLEEP_S:
                self.state = f"💤 sleep {self.CYCLE_SLEEP_S - dt:.1f}s"
                if self.need_stop:
                    break
                await asyncio.sleep(min(1, (self.CYCLE_SLEEP_S - dt) / 2))
