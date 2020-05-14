from core import AttributeStorage, Attribute


class MDC(AttributeStorage):
    x = Attribute(default=lambda: dict())


def test_default_callable():
    a = MDC()
    b = MDC()

    assert a.x is not None
    assert b.x is not None

    assert isinstance(a.x, dict)
    assert isinstance(b.x, dict)

    assert a.x is not b.x

    a.x[1] = 1
    assert 1 not in b.x

    b.x[2] = 2
    assert 2 not in a.x
