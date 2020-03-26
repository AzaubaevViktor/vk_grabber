from typing import List

import pytest

from vk_utils import VKUser, VKPost


@pytest.mark.parametrize('count', (0, 1, 10, 100, 200))
@pytest.mark.parametrize('use_id', (True, False))
def test_users_posts(vk, group_users: List[VKUser], use_id, count):
    user = group_users[0]

    _id = user.uid if use_id else user

    posts = vk.user_posts(_id, count=count)

    for post in posts:
        assert isinstance(post, VKPost)

    assert len(posts) == count
