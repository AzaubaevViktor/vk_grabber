import asyncio
import itertools

from core import LoadConfig, Log
from time_series.ts import TSManager, Funcs
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

    def draw_word(fig, word_ts, name=None):
        x = word_ts.data.keys()
        # corresponding y axis values
        y = word_ts.data.values()

        lists = sorted(zip(*[x, y]))
        new_x, new_y = list(zip(*lists))

        from datetime import datetime
        x_dt = [datetime.fromtimestamp(ts) for ts in new_x]

        fig.add_trace(go.Scatter(x=x_dt, y=new_y, name=name))

    fig = go.Figure()

    draw_word(fig, words[0].sampling(36000, Funcs.divide), "Sampled div")
    draw_word(fig, words[0].sampling(36000, Funcs.simple), "Sampled")
    draw_word(fig, words[0], "Orig")

    fig.show()

asyncio.run(main(100))
