import pytest

from vk_utils import VKUser


pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize("count", (1, 10, 100, 1000))
async def test_vk_persons(vk, group_id, count):
    users = await vk.group_user_ids(group_id, count=count)

    for user in users:
        assert isinstance(user, int)

    assert len(users) == count

