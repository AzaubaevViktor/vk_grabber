import random
from typing import List

import pytest

from vk_utils import VKPerson, VKPost


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('count', (1, 10, 100, 200))
async def test_users_posts(vk, group_users: List[int], count):
    users = random.choices(group_users, k=5)

    for user in users:
        posts = await vk.person_posts(user, count=count)

        for post in posts:
            assert isinstance(post, VKPost)

        assert len(posts) <= count


async def test_user_info(vk, group_users):
    users = await vk.persons_info(group_users)

    for user in users:
        assert isinstance(user, VKPerson)
