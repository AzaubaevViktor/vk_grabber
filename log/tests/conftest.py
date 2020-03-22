import pytest

from log import Log


@pytest.fixture(scope='function')
def log():
    log_object = Log("test")

    yield log_object


