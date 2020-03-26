import asyncio

import pytest

from core import LoadConfig
from vk_utils import VK, VKUser


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def vk():
    config = LoadConfig()

    vk = VK(config.vk)

    await vk.warm_up()

    yield vk

    await vk.shutdown()


@pytest.fixture(scope="session")
def group_id():
    return 55293029


@pytest.fixture(scope='session')
def group_users(vk, group_id):
    users = vk.group_users(group_id, count=50)

    for user in users:
        assert isinstance(user, VKUser)

    return users