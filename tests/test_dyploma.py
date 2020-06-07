import pytest

from dyploma.app import DyplomaApplication
from dyploma.models import State
from dyploma.services.vk_ng import LoadPersonFromGroup, LoadPostFromPerson
from dyploma.services.word_ import WordKnifePost
from vk_utils import VKGroup, VKPerson, VKPost

pytestmark = pytest.mark.asyncio


@pytest.yield_fixture(scope='session')
def event_loop(request):
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def app_ctx(config):
    app = DyplomaApplication(config, force_clean=True)
    await app.warm_up()
    await app()

    return app.ctx


async def test_app(app_ctx):
    assert app_ctx
    print("Now we can start tests")


async def test_groups(app_ctx):
    groups = []

    async for group_raw in app_ctx.db.find_raw(VKGroup):
        assert group_raw.get(LoadPersonFromGroup.FIELD_NAME) == State.FINISHED
        groups.append(group_raw)

    assert len(groups) == 3


async def test_users(app_ctx):
    users = []

    downloaded = 0

    async for user_raw in app_ctx.db.find_raw(VKPerson):
        downloaded += user_raw.get(LoadPostFromPerson.FIELD_NAME) == State.FINISHED
        users.append(user_raw)

    assert len(users) <= app_ctx.participants_count * len(app_ctx.started_groups)
    assert downloaded


async def test_posts(app_ctx):
    posts = []

    downloaded = 0

    async for post_raw in app_ctx.db.find_raw(VKPost):
        downloaded += post_raw.get(WordKnifePost.FIELD_NAME) == State.FINISHED
        posts.append(post_raw)

    assert len(posts) <= app_ctx.participants_count * app_ctx.posts_count
    assert downloaded
