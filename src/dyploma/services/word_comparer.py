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

    def sorted_function(self, item: ComparesResult):
        return item.score


class WordsComparer(BaseWorkApp):
    CYCLE_SLEEP_S = 16

    async def formulae(self, word_source: TimeSeries, word_other: TimeSeries):
        return abs(word_source.sum() - word_other.sum())

    async def main_cycle(self):
        while not self.need_stop:
            # last_update = time()

            for word_source in WordsUpdater.page.data:  # type: WordPage
                if word_source.ts is None:
                    continue
                if word_source.compares_results is None:
                    word_source.compares_results = Compares()

                for word_other in WordsUpdater.page.data:  # type: WordPage
                    if word_source.ts is None:
                        continue

                    score = float(await self.formulae(
                        word_source.ts,
                        word_other.ts
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
