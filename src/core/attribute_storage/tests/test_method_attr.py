import pytest

from core import AttributeStorage, Attribute


class MethodOne(AttributeStorage):
    def _calc(self):
        return self.a * 2

    a = Attribute()
    a2 = Attribute(method=_calc)


class MethodTwo(AttributeStorage):
    a = Attribute()

    @Attribute.property
    def a2(self):
        return self.a * 2


@pytest.mark.parametrize('Class', (
    MethodOne, MethodTwo
))
def test_property(Class):
    obj = Class(a=10)

    assert obj.a == 10
    assert obj.a2 == 20

    obj.a = 20
    assert obj.a2 == 40
