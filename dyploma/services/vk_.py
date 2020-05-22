from app.base import BaseWorkApp, AppContext
from dyploma.services._base import _ChooseModelByField
from vk_utils import VKGroup, VKPerson, VKPost


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


class LoadParticipants(_ChooseModelByField):
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
        user = VKPerson(id=person_id)
        await self.db.store(
            user,
            rewrite=False
        )


class LoadPosts(_ChooseModelByField):
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
    MODEL_CLASS = VKPerson

    async def process(self, user: VKPerson):
        async for post in self.vk.person_posts_iter(person_id=user.id, count=self.posts_count):
            yield post


class LoadPostComments(_ChooseModelByField):
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