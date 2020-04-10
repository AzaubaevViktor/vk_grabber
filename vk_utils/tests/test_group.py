import pytest

from vk_utils import VKGroup, VKComment

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("count", (1, 10, 100, 1000))
async def test_vk_persons(vk, group_id, count):
    users = await vk.group_user_ids(group_id, count=count)

    for user in users:
        assert isinstance(user, int)

    assert len(users) == count


async def test_vk_persons_none(vk, group_id):
    users = await vk.group_user_ids(group_id)

    for user in users:
        assert isinstance(user, int)

    assert len(users) != 0


async def test_group_info(vk, group_id):
    group_info = await vk.group_info(group_id)

    assert isinstance(group_info, VKGroup)

    assert "НГУ" in group_info.name


async def test_group_comments(vk, group_id):
    comments_found = 0
    async for post in vk.group_posts_iter(group_id, count=10):
        is_found = False
        async for comment in vk.comments_iter(owner_id=-group_id, post_id=post.id):
            assert isinstance(comment, VKComment)
            assert comment.from_id == -group_id
            assert comment.date
            assert comment.text is not None

        comments_found += is_found

        if comments_found >= 2:
            break

    assert comments_found >= 2
