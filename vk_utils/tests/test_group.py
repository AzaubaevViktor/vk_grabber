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

    assert len(users) > 100


async def test_group_info(vk, group_id):
    group_info = await vk.group_info(group_id)

    assert isinstance(group_info, VKGroup)

    assert "НГУ" in group_info.name


@pytest.mark.parametrize('owner_id', (
        -182873218,
        78800031
))
async def test_group_comments(vk, owner_id):
    comments_found = 0

    if owner_id < 0:
        posts_iter = vk.group_posts_iter(-owner_id, count=10)
    else:
        posts_iter = vk.user_posts_iter(owner_id, count=10)

    async for post in posts_iter:
        is_found = False
        async for comment in vk.comments_iter(owner_id=owner_id, post_id=post.id):
            if comment.deleted:
                continue
            assert isinstance(comment, VKComment)
            assert comment.from_id
            assert comment.date
            assert comment.text is not None

            assert comment.post_id == post.id
            assert comment.owner_id == owner_id

            comment.verificate()

            is_found = True

        comments_found += is_found

        if comments_found >= 2:
            break

    assert comments_found >= 2
