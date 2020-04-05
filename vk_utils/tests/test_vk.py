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

    assert group_info.id == group_id
    assert group_info.description


async def test_group_no_args(vk, group_id):
    with pytest.raises(ValueError):
        await vk.group_posts(group_id)


@pytest.mark.parametrize('count', (-100, -55, -1, 0))
async def test_group_count_wrong(vk, group_id, count):
    with pytest.raises(ValueError):
        await vk.group_posts(group_id)


@pytest.mark.parametrize('count', (1, 5, 10, 14, 250, 100, 200))
async def test_group_posts_with_count(vk, group_id, count):
    posts = await vk.group_posts(group_id, count=count)

    assert len(posts) == count

    for post in posts:
        assert isinstance(post, VKPost)
        assert post.from_id == -group_id

    if len(posts) > 2:
        assert posts[0].date > posts[-1].date

    uids = set(post.id for post in posts)
    assert len(uids) == len(posts)


class TestGroupPostTs:
    @pytest.fixture(scope='class')
    async def last_posts(self, vk, group_id) -> List[VKPost]:
        posts = await vk.group_posts(group_id, count=10)
        assert len(posts) == 10
        return posts

    @pytest.mark.xfail(reason="Download by ts not implemented yet")
    @pytest.mark.parametrize('index', range(9))
    async def test_group_posts_with_ts(self, vk, group_id, last_posts, index):
        assert len(last_posts) > index + 1

        posts_ts = await vk.group_posts(group_id,
                                        from_ts=(last_posts[index].date + last_posts[index + 1].date) / 2)

        assert len(posts_ts) == index
        assert posts_ts == last_posts[:index]


async def test_wrong(vk, group_id):
    with pytest.raises(ValueError):
        await vk.group_posts(group_id, from_ts=100, count=100)
