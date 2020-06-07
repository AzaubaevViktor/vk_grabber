from pprint import pprint

import pytest

from vk_utils import VK

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize('user_id', (50272981, ))
async def test_user_deleted(vk: VK, user_id):
    users = await vk.persons_info(user_id)
    assert len(users) == 1
    user = users[0]
    assert user.deactivated


@pytest.mark.parametrize('user_id', (632055, ))
async def test_access_to_comments(vk: VK, user_id):
    users = await vk.persons_info(user_id)
    assert len(users) == 1
    user = users[0]

    data = user.serialize()
    pprint(data)

    async for post in vk.person_posts_iter(user_id, count=10):
        assert not post.comments['can_post']
        pprint(post.serialize())


@pytest.mark.parametrize('user_id', (2045237, ))
async def test_private(vk: VK, user_id):
    users = await vk.persons_info(user_id)
    assert len(users) == 1
    user = users[0]

    assert user.is_closed
