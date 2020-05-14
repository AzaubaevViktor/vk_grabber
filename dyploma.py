import asyncio

from app.base import BaseApplication, AppContext, BaseWorkApp
from core import LoadConfig, BaseWork
from database import Model, ModelAttribute
from vk_utils import VKGroup, VKUser, VKPost, VKComment
from word_worker import tokenize


class LoadGroups(BaseWorkApp):
    INPUT_RETRIES = 0

    async def input(self):
        for item in self.ctx.started_groups:
            yield item

    async def process(self, item: int):
        item = int(item)
        yield VKGroup(id=item)

    async def update(self, result):
        await self.db.store(result, rewrite=False)


class _LoadModelField(BaseWorkApp):
    MODEL_CLASS = None
    FIELD_NAME = None
    INPUT_QUERY_LIMIT = 5

    async def warm_up(self):
        # Clean field=False
        assert self.MODEL_CLASS
        assert self.FIELD_NAME

        count = 0
        async for _ in self.db.choose(self.MODEL_CLASS, {self.FIELD_NAME: False},
                                      {self.FIELD_NAME: None}):
            count += 1

        self.log.info("Cleanup old tasks", count=count)

    async def input(self):
        async for item in self.db.choose(self.MODEL_CLASS, {self.FIELD_NAME: None},
                                         {self.FIELD_NAME: False},
                                         limit_=self.INPUT_QUERY_LIMIT):
            yield item, self.db.store(item, **{self.FIELD_NAME: True})


class LoadParticipants(_LoadModelField):
    INPUT_RETRIES = 3

    MODEL_CLASS = VKGroup
    FIELD_NAME = "load_persons"
    INPUT_QUERY_LIMIT = 1

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        self.participants_count = self.ctx.participants_count

    async def process(self, group: VKGroup):
        async for person_id in self.vk.group_participants_iter(
                group.id, count=self.participants_count
        ):
            yield person_id

    async def update(self, person_id):
        user = VKUser(id=person_id)
        await self.db.store(
            user,
            rewrite=False
        )


class LoadPosts(_LoadModelField):
    FIELD_NAME = "load_posts"

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        self.posts_count = self.ctx.posts_count

    async def update(self, post: VKPost):
        if not post.text:
            return

        await self.db.store(
            post,
            rewrite=False
        )


class LoadGroupPosts(LoadPosts):
    INPUT_RETRIES = 3
    MODEL_CLASS = VKGroup

    async def process(self, group: VKGroup):
        async for post in self.vk.group_posts_iter(
                group.id, count=self.posts_count
        ):
            yield post


class LoadPersonsPosts(LoadPosts):
    INPUT_RETRIES = 3
    MODEL_CLASS = VKUser

    async def process(self, user: VKUser):
        async for post in self.vk.user_posts_iter(user_id=user.id, count=self.posts_count):
            yield post


class LoadPostComments(_LoadModelField):
    INPUT_RETRIES = 5

    MODEL_CLASS = VKPost
    FIELD_NAME = "load_comments"

    async def process(self, post: VKPost):
        async for comment in self.vk.comments_iter(owner_id=post.owner_id, post_id=post.id):
            yield comment
            for thread_comment in comment.get_thread():
                yield thread_comment

    async def update(self, comment):
        if not comment.text:
            return

        if comment.deleted:
            return

        await self.db.store(
            comment
        )


class Word(Model):
    word: str = ModelAttribute()
    date: int = ModelAttribute()
    from_id: int = ModelAttribute()
    post_id: int = ModelAttribute()


class BaseWordKnife(_LoadModelField):
    INPUT_RETRIES = 5
    MODEL_CLASS = None
    FIELD_NAME = 'word_processed'

    async def process(self, post: VKPost):
        for word in tokenize(post.text):
            yield Word(word=word,
                       post_id=post.id,
                       from_id=post.from_id,
                       date=post.date,)

    async def update(self, word: Word):
        await self.db.store(
            word
        )


class WordKnifePost(BaseWordKnife):
    MODEL_CLASS = VKPost


class WordKnifeComment(BaseWordKnife):
    MODEL_CLASS = VKComment


class Application(BaseApplication):
    def __init__(self, config: LoadConfig, force_clean=False):
        super().__init__(config)
        self.clean = config.app.clean
        self._force_clean = force_clean

    async def warm_up(self):
        if self.clean:
            if not self._force_clean:
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

            self.log.important("⚠️ ⚠️ ⚠️ HERE WE DROP DATABASE")
            await self.ctx.db.delete_all(i_understand_delete_all=True)
            self.log.important("⚠️ ⚠️ ⚠️ HERE WE END DROP DATABASE...")

        await super(Application, self).warm_up()

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
