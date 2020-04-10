import asyncio
from typing import List, Sequence

import motor.motor_asyncio
import pymongo.errors

from plotly import graph_objects as go

from core import LoadConfig, Log, Time, BaseWork
from core.chaos import Chaos
from database import DBWrapper
from time_series.ts import TSManager, TimeSeries, Funcs
from vk_utils import VK, VKGroup, VKUser, VKPost
from word_woker import tokenize


class BaseApplication:
    def __init__(self, config: LoadConfig,
                 posts_count, persons_count, users_count):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.vk = VK(config.vk)
        self.db = DBWrapper(
            motor.motor_asyncio.AsyncIOMotorClient(
                config.mongo.uri
            ),
            config.mongo.database
        )

        self.posts_count = posts_count
        self.persons_count = persons_count
        self.users_count = users_count or float("+inf")

    async def warm_up(self):
        await self.vk.warm_up()


class BaseWorkApp(BaseWork):
    def __init__(self, db: DBWrapper, vk: VK):
        super().__init__()
        self.db = db
        self.vk = vk
        self.state = f"{BaseWorkApp.__name__} initialized"


class LoadGroups(BaseWorkApp):
    def __init__(self, *args, groups):
        super().__init__(*args)
        self.groups = groups

    async def input(self):
        for item in self.groups:
            yield item

    async def process(self, item: int):
        item = int(item)
        yield VKGroup(_id=item)

    async def update(self, result):
        # TODO: Cache
        try:
            await self.db.insert_many(result, force=True)
        except pymongo.errors.BulkWriteError:
            self.log.exception("Exist")


class LoadPersons(BaseWorkApp):
    def __init__(self, db: DBWrapper, vk: VK, persons_count=None):
        super().__init__(db, vk)
        self.persons_count = persons_count

    async def input(self):
        async for item in self.db.find(VKGroup(), load_persons=None):
            yield item

    async def process(self, group: VKGroup):
        await self.db.update(group, load_persons=True)
        async for person_id in self.vk.group_participants_iter(
                group.id, count=self.persons_count
        ):
            yield person_id

    async def update(self, person_id):
        try:
            await self.db.insert_many(
                VKUser(_id=person_id),
                force=True
            )
        except pymongo.errors.BulkWriteError:
            # Model already exist
            pass


class LoadPosts(BaseWorkApp):
    MODEL = None

    def __init__(self, db: DBWrapper, vk: VK, posts_count=None):
        super().__init__(db, vk)
        self.posts_count = posts_count

    async def input(self):
        async for item in self.db.find(self.MODEL(), load_posts=None):
            yield item

    async def update(self, post):
        if not post.text:
            return

        try:
            await self.db.insert_many(
                post,
                force=True
            )
        except pymongo.errors.BulkWriteError:
            # Model already exist
            pass


class LoadGroupPosts(LoadPosts):
    MODEL = VKGroup

    async def process(self, group: VKGroup):
        await self.db.update(group, load_posts=True)
        async for post in self.vk.group_posts_iter(
                group.id, count=self.posts_count
        ):
            yield post


class LoadPersonsPosts(LoadPosts):
    INPUT_REPEATS = 3
    MODEL = VKUser

    async def process(self, user: VKUser):
        await self.db.update(user, load_posts=True)

        async for post in self.vk.user_posts_iter(user_id=user.id, count=self.posts_count):
            yield post


class Application(BaseApplication):
    def __init__(self, config: LoadConfig,
                 posts_count, persons_count, users_count,
                 clean=True):
        super().__init__(config, posts_count, persons_count, users_count)
        self.clean = clean

    async def warm_up(self):
        if self.clean:
            await self.db.delete_all(i_understand_delete_all=True)
        await self.vk.warm_up()

    async def __call__(self):
        await asyncio.gather(
            LoadGroups(self.db, self.vk, groups=self.config.vk.groups)()
        )

        await asyncio.gather(
            LoadPersons(self.db, self.vk, persons_count=self.persons_count)(),
            LoadPersonsPosts(self.db, self.vk, posts_count=self.posts_count)(),
            LoadGroupPosts(self.db, self.vk, posts_count=self.posts_count)()
        )


def simple_bunches(datas: Sequence, count: int):
    parts = len(datas) // count + 1
    for i in range(parts):
        s = datas[i * count:(i + 1) * count]
        if s:
            yield s

    assert (i + 1) * count >= len(datas)


class __Application(BaseApplication):
    def __init__(self, *args, cleanup=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.cleanup = cleanup
        self.log.info("Application initialized")

    async def load_groups(self):
        self.log.info("Load group service started!")
        with self.neo4j.session() as session:
            session.write_transaction(create_nodes, *(
                VKGroup.dummy(id=_id)
                for _id in self.config.vk.groups
            ))
        self.log.info("Load group service finished!")

    async def load_group_info(self):
        self.log.info("Load group info started")

        # Load data
        with self.neo4j.session() as session:
            found_dummy_nodes = session.read_transaction(find_nodes, VKGroup.Dummy())

        for node in found_dummy_nodes:
            self.log.debug("Process", node=node)
            assert isinstance(node, VKGroup.Dummy())

            group = await self.vk.group_info(node.id)

            with self.neo4j.session() as session:
                session.write_transaction(update_node, group)

        self.log.info("Load group info finished!")

    async def load_group_persons(self):
        self.log.info("Load persons from group!")

        with self.neo4j.session() as session:
            groups = session.read_transaction(find_nodes, VKGroup)

        for group in groups:
            group = group.undummy()
            self.log.debug("Load persons", group=group)
            person_ids = await self.vk.group_user_ids(group.id, count=self.persons_count)

            self.log.info(group=group.id, users_count=len(person_ids))
            users_dummy = tuple(VKUser.dummy(id=id_, is_checked=False) for id_ in person_ids)

            for users in simple_bunches(users_dummy, 10):
                self.log.debug("Prepare transaction", count=len(users))
                with self.neo4j.session() as session:
                    session.write_transaction(do_links, group, Participant(), users)
                    self.log.debug("Write transaction")
                self.log.debug("Finished transaction")
                await asyncio.sleep(0)

    async def load_group_posts(self):
        self.log.info("Load group posts")

        with self.neo4j.session() as session:
            groups = session.read_transaction(find_nodes, VKGroup)

        for group in groups:
            group = group.undummy()
            all_posts = await self.vk.group_posts(group_id=group.id, count=self.posts_count)

            await self._process_posts(all_posts, group)

        self.log.info("Load group posts finished")

    async def _process_posts(self, all_posts, group):
        for posts in simple_bunches(all_posts, 100):
            self.log.info("Write posts from", group=group, count=len(posts))

            self.posts.insert_many((
                dict(post) for post in posts
            ))

    async def load_person_posts(self):
        self.log.info("Load person posts")

        users_count = 0

        while users_count < self.users_count:
            with self.neo4j.session() as session:
                users = session.read_transaction(find_nodes, VKUser, is_checked=False, limit=20)
                for user in users:
                    user.is_checked = True
                    session.write_transaction(update_node, user)

            if not len(users):
                await asyncio.sleep(1)
                continue

            for user in users:
                all_posts = await self.vk.user_posts(user_id=user.id, count=self.posts_count)

                await self._process_posts(all_posts, user)

            users_count += len(users)
            self.log.important("Processed users:", count=users_count)

        self.log.info("Load person posts finished")

    async def __call__(self):
        self.log.important("Hi there! Application v2 here")

        if self.cleanup:
            self.log.warning("⚠️ NOW WE CLEAN DATABASE")
            self.log.info("Clean neo4j")
            with self.neo4j.session() as session:
                session.run("MATCH (n) DETACH DELETE n")

            self.log.info("Clean mongo")
            self.posts.delete_many({})

            self.log.warning("👍 WE CLEAN DATABASE")
            self.log.warning("If you donn't wanna to, set `cleanup` parameter to False")

        await self.load_groups()

        results = await asyncio.gather(
            self.load_group_info(),
            self.load_group_persons(),
            self.load_group_posts(),
            self.load_person_posts()
        )

        self.log.important(results)


class _Application(BaseApplication):
    def __init__(self, config: LoadConfig, posts_count):
        super().__init__(config, posts_count)
        self.tsm = TSManager()

    async def _load_group_posts(self):
        self.log.info("Load posts from groups")
        group_ids = self.config.vk.groups

        posts = sum(await asyncio.gather(*(
            self.vk.group_posts(group_id=group_id, count=self.posts_count)
            for group_id in group_ids
        )), [])

        return posts

    async def _load_persons(self):
        raise NotImplementedError()

    def _process_posts(self, posts):
        self.log.info("Process posts", count=len(posts))

        for post in posts:
            words = tokenize(post.text)

            for word in words:
                self.tsm.add(word, post.date, 1)

    def _find_interested(self):
        def f(word: TimeSeries):
            if len(word) >= 2:
                return word.max_value() / word.mid_value()
            return 0

        words = self.tsm.sorted_by(f)

        self.log.info("Found words", count=len(words))
        for index in range(5):
            self.log.debug(index=index,
                           word=words[index],
                           score=f(words[index]))

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

        for word in words[2:5]:
            period = word.med_d_ts()

            self.log.info(word=word, period=Time(period), mid=Time(word.mid_d_ts()))

            self._draw_word(fig, word, opacity=0.6, mode='markers')

            self._draw_word(fig, word.sampling(period, Funcs.spline(80)))
            self._draw_word(fig, word.sampling(period, Funcs.spline(80)).d())
            self._draw_word(fig, word.sampling(period, Funcs.spline(160)))
            self._draw_word(fig, word.sampling(period, Funcs.spline(160)).d())

        fig.show()

    async def __call__(self):
        posts = await self._load_group_posts()
        self._process_posts(posts)

        words = self._find_interested()
        self._do_draw(words)