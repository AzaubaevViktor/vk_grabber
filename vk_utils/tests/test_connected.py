import pytest


pytestmark = pytest.mark.asyncio


async def test_simple(vk):
    user_info = await vk.user_info()

    assert isinstance(user_info, AttributeStorage)

