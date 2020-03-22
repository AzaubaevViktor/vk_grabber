import pytest

from core import LoadConfig


@pytest.fixture(scope='session')
def vk():
    config = LoadConfig()

    vk = VK(config.vk)

    return vk


@pytest.fixture(scope="session")
def test_group_id():
    raise NotImplementedError()
    return None
