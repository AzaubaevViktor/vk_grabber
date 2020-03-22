from core import LoadConfig


def test_attr():
    config = LoadConfig("core/config/tests/test.yaml")
    assert config.a == {'x': 123, 'y': 456, "z": "Hello, world!"}
    assert config.test == [1, 2, 3, 4]
