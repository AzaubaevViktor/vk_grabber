import asyncio
from typing import List

from plotly import graph_objects as go

from core import LoadConfig, Log, Time
from time_series.ts import TSManager, TimeSeries, Funcs
from vk_utils import VK
from word_woker import tokenize


class Application:
    def __init__(self, config: LoadConfig, posts_count):
        self.log = Log("Application")
        self.config = config
        self.vk = VK(config.vk)
        self.posts_count = posts_count
        self.tsm = TSManager()

        self._warm_upped = False

    async def warm_up(self):
        assert not self._warm_upped, "Already warm_upped"
        await self.vk.warm_up()

    async def _load_group_posts(self):
        self.log.info("Load posts from groups")
        group_ids = self.config.vk['groups']

        posts = sum(await asyncio.gather(*(
            self.vk.group_posts(group_id=group_id, count=self.posts_count)
            for group_id in group_ids
        )), [])

        return posts

    def _process_posts(self, posts):
        self.log.info("Process posts", count=len(posts))

        for post in posts:
            words = tokenize(post.text)

            for word in words:
                self.tsm.add(word, post.date, 1)

    def _find_interested(self):
        words = self.tsm.sorted_by(lambda ts: ts.sum())

        self.log.info("Found words", count=len(words))
        for index in range(5):
            self.log.debug(index=index,
                           word=words[index],
                           score=words[index].sum())

        return words

    def _draw_word(self, fig, word_ts: TimeSeries,
                   name=None, opacity=None, mode=None):
        if name is None:
            name = word_ts.name

        word_ts.sort()

        x = tuple(word_ts.data.keys())
        # corresponding y axis values
        y = tuple(word_ts.data.values())

        from datetime import datetime
        x_dt = [datetime.fromtimestamp(ts) for ts in x]

        fig.add_trace(go.Scatter(x=x_dt, y=y,
                                 name=name, opacity=opacity,
                                 mode=mode))

    def _do_draw(self, words: List[TimeSeries]):
        fig = go.Figure()

        word = None

        for ts in words:
            if ("нгу" == ts.name) or ('nsu' == ts.name):
                if word is None:
                    word = ts
                else:
                    word += ts

        word = word or words[-1]
        period = word.med_d_ts()

        self.log.info(word=word, period=Time(period), mid=Time(word.mid_d_ts()))

        self._draw_word(fig, word, opacity=0.6, mode='markers')
        # draw_word(fig, word.int(), opacity=0.6, mode='markers')

        # draw_word(fig, word.sampling(period, Funcs.simple), "Sampled", opacity=0.3)
        # draw_word(fig, word.sampling(period, Funcs.divide), "Sampled div", opacity=0.3)
        # draw_word(fig, word.sampling(period, Funcs.spline(1)))
        # draw_word(fig, word.sampling(period, Funcs.spline(2)))
        # draw_word(fig, word.sampling(period, Funcs.spline(4)), "Spline 4", mode='markers')
        # draw_word(fig, word.sampling(period, Funcs.spline(8)))
        # draw_word(fig, word.sampling(period, Funcs.spline(80)).int())
        # draw_word(fig, word.sampling(period, Funcs.spline(40)).int())
        # draw_word(fig, word.sampling(period, Funcs.spline(20)).int())
        # draw_word(fig, word.sampling(period, Funcs.spline(2)).int())

        self._draw_word(fig, word.sampling(period, Funcs.spline(8)))
        self._draw_word(fig, word.sampling(period, Funcs.spline(8)).d())
        self._draw_word(fig, word.sampling(period, Funcs.spline(16)))
        self._draw_word(fig, word.sampling(period, Funcs.spline(16)).d())

        fig.show()

    async def __call__(self):
        posts = await self._load_group_posts()
        self._process_posts(posts)

        words = self._find_interested()
        self._do_draw(words)