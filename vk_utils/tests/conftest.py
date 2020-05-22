import asyncio

import pytest

from vk_utils import VK


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def vk(config):
    assert config.app.test

    vk = VK(config.vk)

    await vk.warm_up()

    yield vk

    await vk.shutdown()


@pytest.fixture(scope="session")
def group_id():
    return 128668497


@pytest.fixture(scope='session')
async def group_users(vk, group_id):
    users = await vk.group_user_ids(group_id, count=50)

    for user in users:
        assert isinstance(user, int)

    return users
