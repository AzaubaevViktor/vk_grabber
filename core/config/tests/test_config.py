import pytest

from core import LoadConfig


def test_attr(config: LoadConfig):
    assert config.a == {'x': 123, 'y': 456, "z": "Hello, world!"}
    assert config.test == [1, 2, 3, 4]


def test_subattr(config: LoadConfig):
    assert config.a.x == 123
    assert config.suba.subb.subc.subd == 123


def test_wrong(config: LoadConfig):
    with pytest.raises(KeyError) as e:
        assert not config.a.non_existen

    assert "x" in str(e)
    assert "y" in str(e)
    assert "z" in str(e)
    assert "non_existen" in str(e)


@pytest.mark.parametrize(
    "path", (('first', ), ('a', 'x'))
)
def test_update_exist_first(config: LoadConfig, config_file: str, path):
    def read(cfg):
        result = cfg
        for item in path:
            result = getattr(result, item)

        assert isinstance(result, int)

        return result

    def update(cfg, value):
        result = cfg
        for item in path[:-1]:
            result = getattr(result, item)

        setattr(result, path[-1], value)

    old_value = read(config)
    new_value = old_value ** 2 + 5

    update(config, new_value)
    assert read(config) == new_value

    assert read(LoadConfig(config_file)) == old_value

    config.update()

    assert read(LoadConfig(config_file)) == new_value


@pytest.mark.parametrize('path', (('non_exist', ), ('a', 'ne'), ('suba', 'subb', 'subc', 'ne')))
def test_update_nonexisten(config: LoadConfig, path):
    result = config
    for item in path:
        result = getattr(result, item)

    with pytest.raises(KeyError):
        setattr(result, path[-1], 100)
