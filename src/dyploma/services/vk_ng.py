from app.base import BaseWorkApp, AppContext
from dyploma.models import State
from dyploma.services._base import _ChooseModelByField
from vk_utils import VKGroup, VKPerson, VKPost


# GROUP

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


class LoadGroupInfo(_ChooseModelByField):
    MODEL_CLASS = VKGroup

    async def process(self, group: VKGroup):
        yield await self.vk.group_info(group_id=group.id)

    async def update(self, group: VKGroup):
        await self.db.store(group, rewrite=False)


# PERSON


class LoadPersonFromGroup(_ChooseModelByField):
    MODEL_CLASS = VKGroup

    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        self.participants_count = self.ctx.participants_count

    async def process(self, group: VKGroup):
        async for person_id in self.vk.group_participants_iter(
                group_id=group.id, count=self.participants_count):
            yield VKPerson(id=person_id)

    async def update(self, person: VKPerson):
        await self.db.store(person, rewrite=False)


class LoadPersonInfo(_ChooseModelByField):
    MODEL_CLASS = VKPerson

    async def process(self, person_: VKPerson):
        for person in await self.vk.persons_info(person_.id):
            yield person

    async def update(self, person: VKPerson):
        await self.db.store(person, rewrite=False)


# POST


class _PostLoader(_ChooseModelByField):
    def __init__(self, ctx: AppContext):
        super().__init__(ctx)
        self.posts_count = self.ctx.posts_count

    async def update(self, post: VKPost):
        if not post.text:
            return

        await self.db.store(post, rewrite=False)


class LoadPostFromGroup(_PostLoader):
    MODEL_CLASS = VKGroup

    async def process(self, group: VKGroup):
        async for post in self.vk.group_posts_iter(group_id=group.id,
                                                   count=self.posts_count):
            yield post


class LoadPostFromPerson(_PostLoader):
    MODEL_CLASS = VKPerson

    ADDITIONAL_FILTER = {
        # TODO: After metaclass, Use .FIELD_NAME
        LoadPersonInfo.__name__: State.FINISHED,
        VKPerson.deactivated.name: None,
        VKPerson.hidden.name: False,
        VKPerson.is_closed.name: False,
    }

    async def process(self, person: VKPerson):
        async for post in self.vk.person_posts_iter(person_id=person.id,
                                                    count=self.posts_count):
            yield post
