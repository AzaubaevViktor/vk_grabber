import os
import tempfile

import pytest

from core import LoadConfig


@pytest.fixture(scope='function')
def _orig_config_path():
    return "core/config/tests/test.yaml"


@pytest.fixture(scope='function')
def config_file(_orig_config_path):
    file = tempfile.NamedTemporaryFile(mode='wt', delete=False)
    with open(_orig_config_path, "rt") as f:
        file.file.write(f.read())
    file.close()

    yield file.name

    os.remove(file.name)


@pytest.fixture(scope='function')
def config(config_file):
    return LoadConfig(config_file)
