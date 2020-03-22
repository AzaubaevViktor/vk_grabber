import asyncio
import itertools

from core import LoadConfig, Log
from time_series.ts import TSManager
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

    word_ts = words[0]

    # importing the required module
    import matplotlib.pyplot as plt

    # x axis values
    x = word_ts.data.keys()
    # corresponding y axis values
    y = word_ts.data.values()

    lists = sorted(zip(*[x, y]))
    new_x, new_y = list(zip(*lists))
    print(new_x)
    print(new_y)

    # plotting the points
    from matplotlib import dates
    plt.scatter(new_x, new_y)

    # naming the x axis
    plt.xlabel('TimeStamp')
    # naming the y axis
    plt.ylabel('Value')

    # giving a title to my graph
    plt.title(word_ts.name)

    # function to show the plot
    plt.show()


asyncio.run(main(100))
