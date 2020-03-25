import asyncio
import itertools

from core import LoadConfig, Log
from time_series.ts import TSManager, Funcs, TimeSeries
from vk_utils import VK
from word_woker import tokenize


async def main(count):
    log = Log("main")
    config = LoadConfig()

    vk = VK(config.vk)

    await vk.warm_up()

    log.info("Load posts")
    posts = await vk.group_posts(group_id=37080997, count=count)

    tsm = TSManager()

    log.info("Process posts")
    for post in posts:
        words = tokenize(post.text)

        for word in words:
            tsm.add(word, post.date, 1)

    log.info("Sort by summary")
    words = tsm.sorted_by(lambda ts: ts.sum())

    print(words)
    for index in range(5):
        print(words[index], words[index].sum())

    import plotly.graph_objects as go

    def draw_word(fig, word_ts: TimeSeries, name=None, opacity=None, mode=None):
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

    fig = go.Figure()

    period = 19 * 60 * 60

    draw_word(fig, words[0], opacity=0.6, mode='markers')
    draw_word(fig, words[0].int(), opacity=0.6, mode='markers')

    # draw_word(fig, words[0].sampling(period, Funcs.simple), "Sampled", opacity=0.3)
    # draw_word(fig, words[0].sampling(period, Funcs.divide), "Sampled div", opacity=0.3)
    # draw_word(fig, words[0].sampling(period, Funcs.spline(1)))
    # draw_word(fig, words[0].sampling(period, Funcs.spline(2)))
    # draw_word(fig, words[0].sampling(period, Funcs.spline(4)), "Spline 4", mode='markers')
    # draw_word(fig, words[0].sampling(period, Funcs.spline(8)))
    draw_word(fig, words[0].sampling(period, Funcs.spline(80)).int())
    draw_word(fig, words[0].sampling(period, Funcs.spline(40)).int())
    draw_word(fig, words[0].sampling(period, Funcs.spline(20)).int())
    draw_word(fig, words[0].sampling(period, Funcs.spline(1)).int())

    draw_word(fig, words[0].sampling(period, Funcs.spline(8)))
    draw_word(fig, words[0].sampling(period, Funcs.spline(8)).d())
    draw_word(fig, words[0].sampling(period, Funcs.spline(16)))

    fig.show()

asyncio.run(main(100))
