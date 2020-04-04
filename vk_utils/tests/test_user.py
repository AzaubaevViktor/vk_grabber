import random
from typing import List

import pytest

from vk_utils import VKUser, VKPost


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('count', (0, 1, 10, 100, 200))
async def test_users_posts(vk, group_users: List[int], count):
    users = random.choices(group_users, k=5)

    for user in users:
        posts = await vk.user_posts(user, count=count)

        for post in posts:
            assert isinstance(post, VKPost)

        assert len(posts) == count


async def test_user_info(vk, group_users):
    user_id = group_users[0]

    user = (await vk.users_info(user_id))[0]

    assert isinstance(user, VKUser)
