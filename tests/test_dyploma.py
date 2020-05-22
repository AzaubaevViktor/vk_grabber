import pytest

from dyploma.app import DyplomaApplication
from dyploma.services.vk_ import LoadParticipants, LoadPersonsPosts
from vk_utils import VKGroup, VKPerson

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
        assert group_raw.get(LoadParticipants.FIELD_NAME) is True
        groups.append(group_raw)

    assert len(groups) == 3


async def test_users(app_ctx):
    users = []

    downloaded = 0

    async for user_raw in app_ctx.db.find_raw(VKPerson):
        downloaded += user_raw.get(LoadPersonsPosts.FIELD_NAME) is True
        users.append(user_raw)

    assert len(users)
    assert downloaded
