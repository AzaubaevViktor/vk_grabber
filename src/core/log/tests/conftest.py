import pytest

from core import Log


@pytest.fixture(scope='function')
def log():
    log_object = Log("test")

    yield log_object


