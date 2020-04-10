import pytest

from core import LoadConfig


@pytest.fixture(scope='session')
def config():
    return LoadConfig("configs/test.yaml")
