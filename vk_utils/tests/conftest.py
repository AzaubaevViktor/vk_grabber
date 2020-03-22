import pytest


@pytest.fixture(scope='session')
def vk():
    config = LoadConfig()

    vk = VK(config.vk)

    return vk
