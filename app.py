import asyncio

import motor.motor_asyncio
import pymongo.errors

from core import LoadConfig, Log, BaseWork
from database import DBWrapper, Model, ModelAttribute
from vk_utils import VK, VKGroup, VKUser, VKPost, VKComment
from word_woker import tokenize


class BaseApplication:
    def __init__(self, config: LoadConfig):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.ctx = AppContext(self.config)

    async def warm_up(self):
        await self.ctx.warm_up()


class AppContext:
    def __init__(self, config: LoadConfig):
        self.config = config
        self.stage_name = config.app.stage
        self.vk = VK(config.vk)
        self.db = DBWrapper(
            motor.motor_asyncio.AsyncIOMotorClient(
                config.mongo.uri
            ),
            config.mongo.database
        )

        self.started_groups = config.vk.groups

        self.posts_count = config.app.posts_count
        self.participants_count = config.app.participants_count

    async def warm_up(self):
        await self.vk.warm_up()


class BaseWorkApp(BaseWork):
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.db = self.ctx.db
        self.vk = self.ctx.vk
        self.state = f"{BaseWorkApp.__name__} initialized"


class LoadGroups(BaseWorkApp):
    INPUT_RETRIES = 0

    async def input(self):
        for item in self.ctx.started_groups:
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
    INPUT_RETRIES = 3

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        self.participants_count = self.ctx.participants_count

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

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        assert self.FLAG is not None, "FLAG Unsetted"
        self.posts_count = self.ctx.posts_count

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
    INPUT_RETRIES = 3
    MODEL = VKUser

    async def process(self, user: VKUser):
        async for post in self.vk.user_posts_iter(user_id=user.id, count=self.posts_count):
            yield post


class LoadPostComments(BaseWorkApp):
    INPUT_RETRIES = 20

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


class Word(Model):
    word: str = ModelAttribute()
    date: int = ModelAttribute()
    from_id: int = ModelAttribute()
    post_id: int = ModelAttribute()


class BaseWordKnife(BaseWorkApp):
    INPUT_RETRIES = 5
    MODEL = None

    async def input(self):
        async for post in self.db.find(self.MODEL(), word_processed=None, limit=20):
            yield post, self.db.update(post, word_processed=True)

    async def process(self, post: VKPost):
        for word in tokenize(post.text):
            yield Word(word=word,
                       post_id=post.id,
                       from_id=post.from_id,
                       date=post.date,)

    async def update(self, word: Word):
        await self.db.insert_many(
            word
        )


class WordKnifePost(BaseWordKnife):
    MODEL = VKPost


class WordKnifeComment(BaseWordKnife):
    MODEL = VKComment


class Application(BaseApplication):
    def __init__(self, config: LoadConfig):
        super().__init__(config)
        self.clean = config.app.clean

    async def warm_up(self):
        if self.clean:
            self.log.important("⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️")
            self.log.important("⚠️⚠️⚠️                           ⚠️⚠️⚠️")
            self.log.important("⚠️⚠️⚠️ NOW I DELETE ALL DATABASE ⚠️⚠️⚠️")
            self.log.important(f"⚠️⚠️⚠️{self.ctx.db.db_name:^27}⚠️⚠️⚠️")
            self.log.important("⚠️⚠️⚠️                           ⚠️⚠️⚠️")
            self.log.important("⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️")
            self.log.important("This", name=self.ctx.db.db_name, db=self.ctx.db)
            
            countdown = 10
            for i in range(countdown):
                await asyncio.sleep(1)
                self.log.warning(countdown - i)
            await self.ctx.db.delete_all(i_understand_delete_all=True)

        await self.ctx.warm_up()

        BaseWork.for_monitoring['vk'] = self.ctx.vk.stats
        await BaseWork.run_monitoring_server(self.config.app)

        await self._add_handlers()

    async def __call__(self):
        first = await self.prepare_services(LoadGroups)

        second = await self.prepare_services(
            LoadParticipants,
            LoadPersonsPosts,
            LoadGroupPosts,
            LoadPostComments,
            WordKnifePost,
            WordKnifeComment,
        )

        await first
        await second

    async def prepare_services(self, *services):
        first_step_tasks = []
        for item in services:
            if self.config.app.services[item.__name__]:
                self.log.info("Service postponed", service=item)
                first_step_tasks.append(item(self.ctx)())
            else:
                self.log.info("Service disabled by config", service=item)
        return asyncio.gather(*first_step_tasks)

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
