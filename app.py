import asyncio

import motor.motor_asyncio
import pymongo.errors

from core import LoadConfig, Log, BaseWork
from database import DBWrapper
from vk_utils import VK, VKGroup, VKUser, VKPost, VKComment


class BaseApplication:
    def __init__(self, config: LoadConfig,
                 posts_count=None, participants_count=None, users_count=None):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.vk = VK(config.vk)
        self.db = DBWrapper(
            motor.motor_asyncio.AsyncIOMotorClient(
                config.mongo.uri
            ),
            config.mongo.database
        )

        self.posts_count = posts_count or config.app.posts_count
        self.participants_count = participants_count or config.app.participants_count
        self.users_count = users_count or config.app.users_count or float("+inf")

    async def warm_up(self):
        await self.vk.warm_up()


class BaseWorkApp(BaseWork):
    def __init__(self, db: DBWrapper, vk: VK):
        super().__init__()
        self.db = db
        self.vk = vk
        self.state = f"{BaseWorkApp.__name__} initialized"


class LoadGroups(BaseWorkApp):
    INPUT_REPEATS = 0

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
            self.log.info("Exist", result=result)


class LoadParticipants(BaseWorkApp):
    def __init__(self, db: DBWrapper, vk: VK, participants_count=None):
        super().__init__(db, vk)
        self.participants_count = participants_count

    async def input(self):
        async for group in self.db.find(VKGroup(), load_persons=None, limit=1):
            yield group, self.db.update(group, load_persons=True)

    async def process(self, group: VKGroup):
        async for person_id in self.vk.group_participants_iter(
                group.id, count=self.participants_count
        ):
            yield person_id

    async def update(self, person_id):
        user = VKUser(_id=person_id)
        try:
            await self.db.insert_many(
                user,
                force=True
            )
        except pymongo.errors.BulkWriteError:
            # Model already exist
            self.log.info("Exist", user=user)


class LoadPosts(BaseWorkApp):
    MODEL = None
    FLAG = 'load_posts'

    def __init__(self, db: DBWrapper, vk: VK, posts_count=None):
        super().__init__(db, vk)
        assert self.FLAG is not None, "FLAG Unsetted"
        self.posts_count = posts_count

    async def input(self):
        async for item in self.db.find(self.MODEL(), **{self.FLAG: None}, limit=5):
            yield item, self.db.update(item, **{self.FLAG: True})

    async def update(self, post):
        if not post.text:
            return

        try:
            await self.db.insert_many(
                post,
                force=True
            )
        except pymongo.errors.BulkWriteError:
            self.log.info("Exist", result=post)


class LoadGroupPosts(LoadPosts):
    MODEL = VKGroup

    async def process(self, group: VKGroup):
        async for post in self.vk.group_posts_iter(
                group.id, count=self.posts_count
        ):
            yield post


class LoadPersonsPosts(LoadPosts):
    INPUT_REPEATS = 3
    MODEL = VKUser

    async def process(self, user: VKUser):
        async for post in self.vk.user_posts_iter(user_id=user.id, count=self.posts_count):
            yield post


class LoadPostComments(BaseWorkApp):
    INPUT_REPEATS = 3

    async def input(self):
        async for post in self.db.find(VKPost(), load_comments=None, limit=5):
            yield post, self.db.update(post, load_comments=True)

    async def process(self, post: VKPost):
        async for comment in self.vk.comments_iter(owner_id=post.owner_id, post_id=post.id):
            yield comment
            for thread_comment in comment.get_thread():
                yield thread_comment

    async def update(self, comment):
        if not comment.text:
            return

        try:
            await self.db.insert_many(
                comment
            )
        except pymongo.errors.BulkWriteError:
            self.log.info("Exist", comment=comment)


class Application(BaseApplication):
    def __init__(self, config: LoadConfig,
                 posts_count=None, participants_count=None, users_count=None,
                 clean=True):
        super().__init__(config, posts_count, participants_count, users_count)
        self.clean = clean

    async def warm_up(self):
        if self.clean:
            await self.db.delete_all(i_understand_delete_all=True)
        await self.vk.warm_up()
        BaseWork.for_monitoring['vk'] = self.vk.stats
        await BaseWork.run_monitoring_server()

    async def __call__(self):
        await self._add_handlers()

        await asyncio.gather(
            LoadGroups(self.db, self.vk, groups=self.config.vk.groups)()
        )

        await asyncio.gather(
            LoadParticipants(self.db, self.vk, participants_count=self.participants_count)(),
            LoadPersonsPosts(self.db, self.vk, posts_count=self.posts_count)(),
            LoadGroupPosts(self.db, self.vk, posts_count=self.posts_count)(),
            LoadPostComments(self.db, self.vk)()
        )

    async def _add_handlers(self):
        import signal
        import functools

        loop = asyncio.get_running_loop()
        for signame in {'SIGINT', 'SIGTERM'}:
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(self._gracefull, signame, loop))

    def _gracefull(self, signame, loop):
        self.log.warning("⚠️ Exit handler", signame=signame, loop=loop)
        BaseWork.need_stop = True
