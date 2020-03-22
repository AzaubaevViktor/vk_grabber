from typing import List

import pytest

from vk_utils import VKUser, VKGroup, VKPost

pytestmark = pytest.mark.asyncio


async def test_simple(vk):
    user_info = await vk.me()

    assert isinstance(user_info, VKUser)


async def test_group(vk, group_id):
    group_info = await vk.group_info(group_id)

    assert isinstance(group_info, VKGroup)


async def test_group_all_posts(vk, group_id):
    posts = await vk.group_posts(group_id)

    assert len(posts)

    for post in posts:
        assert isinstance(post, VKPost)
        assert post.group_id == group_id

    assert posts[0].timestamp > posts[-1].timestamp


@pytest.mark.parametrize('count', (0, 1, 5, 10, 14))
async def test_group_posts_with_count(vk, group_id, count):
    posts = await vk.group_posts(group_id, count=count)

    assert len(posts) == count

    for post in posts:
        assert isinstance(post, VKpost)
        assert post.group_id == group_id

    if len(posts) > 2:
        assert posts[0].timestamp > posts[-1].timestamp


class TestGroupPostTs:
    @pytest.fixture(scope='class')
    async def last_posts(self, vk, group_id) -> List[VKPost]:
        posts = await vk.group_posts(group_id, count=10)
        assert len(posts) == 10
        return posts

    @pytest.mark.parametrize('index', range(9))
    async def test_group_posts_with_ts(vk, group_id, last_posts, index):
        assert len(last_posts) > index + 1

        posts_ts = await vk.group_posts(group_id,
                                        from_ts=(last_posts[index].timestamp + last_posts[index + 1].timestamp) / 2)

        assert len(posts_ts) == index
        assert posts_ts == last_posts[:index]

