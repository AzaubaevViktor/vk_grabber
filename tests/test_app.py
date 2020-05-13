import pytest

from app import Application
from vk_utils import VKGroup


pytestmark = pytest.mark.asyncio


@pytest.yield_fixture(scope='session')
def event_loop(request):
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def app_ctx(config):
    app = Application(config, force_clean=True)
    await app.warm_up()
    await app()

    return app.ctx


async def test_groups(app_ctx):
    groups = []

    async for group in app_ctx.db.find(VKGroup):
        groups.append(group)

    assert len(groups) == 3
