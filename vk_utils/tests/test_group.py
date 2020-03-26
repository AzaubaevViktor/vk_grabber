import pytest

from vk_utils import VKUser


@pytest.mark.parametrize("count", (0, 1, 10, 100, 1000))
def test_vk_persons(vk, group_id, count):
    users = vk.group_users(group_id, count=count)

    for user in users:
        assert isinstance(user, VKUser)

    assert len(users) == count

