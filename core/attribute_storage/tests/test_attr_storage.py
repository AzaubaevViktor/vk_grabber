import json

import pytest

from core import AttributeStorage, Attribute, KwargsAttribute


class A1(AttributeStorage):
    a = Attribute(description="a1")
    b = Attribute(description="a1")


class A2(A1):
    b = Attribute(description="a2")
    c = Attribute(description="a2")


class A3(A2):
    c = Attribute(description="a3")
    d = Attribute(description="a3")


def test_attrs_inheritance_a3():
    assert A3.__attributes__['a'].description == "a1"
    assert A3.__attributes__['b'].description == "a2"
    assert A3.__attributes__['c'].description == "a3"
    assert A3.__attributes__['d'].description == "a3"
    assert len(A3.__attributes__) == 4


def test_attr_inheritance_a2():
    assert A2.__attributes__['a'].description == "a1"
    assert A2.__attributes__['b'].description == "a2"
    assert A2.__attributes__['c'].description == "a2"
    assert len(A2.__attributes__) == 3


def test_attr_inheritance_a1():
    assert A1.__attributes__['a'].description == 'a1'
    assert A1.__attributes__['b'].description == 'a1'
    assert len(A1.__attributes__) == 2


@pytest.mark.parametrize(
    'klass', (A1, A2, A3)
)
def test_attrs(klass):
    for k, attr in klass.__attributes__.items():
        assert getattr(klass, k) is attr
        assert attr.name == k


def test_attrs_get_set():
    a1 = A1(a=1, b=2)

    assert a1.a == 1
    assert a1.b == 2

    a1.a = 3
    assert a1.a == 3


def test_attr_get_set_inh():
    a2 = A2(a=1, b=2, c=3)
    assert a2.a == 1
    assert a2.b == 2
    assert a2.c == 3

    a2.c = 4
    assert a2.c == 4


class A4(AttributeStorage):
    first_attr = Attribute()
    second_attr = Attribute()


def test_wrong_init():
    with pytest.raises(TypeError) as exc_info:
        A4(first_attr=1)

    assert "second_attr" in str(exc_info)


def test_wrong_init_extra():
    with pytest.raises(TypeError) as exc_info:
        A4(first_attr=1, second_attr=2, extra_attr=5)

    assert "extra_attr" in str(exc_info)


class AD(AttributeStorage):
    default = Attribute(default=100)
    required = Attribute()


def test_missing_required():
    with pytest.raises(TypeError) as exc_info:
        AD()

    assert "required" in str(exc_info)


def test_default():
    ad = AD(required=500)

    assert ad.default == 100
    assert ad.required == 500

    assert json.loads(ad.serialize())['default']
    assert json.loads(ad.serialize())['default'] == 100


def test_default_value():
    ad = AD(required=500, default=1000)

    assert ad.default == 1000
    assert ad.required == 500


@pytest.mark.parametrize(
    'obj', (AD(required=500),
            AD(required=500, default=1000))
)
def test_default_serialize(obj: AD):
    data = obj.serialize()

    assert AD.deserialize(data) == obj


class AK(AttributeStorage):
    x = Attribute()
    params = KwargsAttribute()


def test_kwargs_meta():
    assert AK.__kwargs_attribute__ is AK.params
    assert "params" not in AK.__attributes__


def test_kwargs():
    params = {'a': 1, 'b': 2, 'c': 3}
    ak = AK(x=10, **params)
    assert ak.x == 10
    assert ak.params is not params
    assert ak.params == params


def test_kwargs_serialize():
    params = {'a': 1, 'b': 2, 'c': 3}
    ak = AK(x=10, **params)

    data = ak.serialize()

    assert data

    obj_r = AK.deserialize(data)

    assert ak.params == obj_r.params, data
    assert ak == obj_r


def test_empty_kwargs():
    ak = AK(x=5)
    assert ak.x == 5
    assert ak.params == {}


def test_two_kwargs():
    with pytest.raises(NameError) as exc_info:
        class XX(AttributeStorage):
            b = Attribute()
            xx_kwargs = KwargsAttribute()
            c = Attribute()
            yy_kwargs = KwargsAttribute()

    assert "xx_kwargs" in str(exc_info)
    assert "yy_kwargs" in str(exc_info)


def test_two_kwargs_inh():
    with pytest.raises(NameError) as exc_info:
        class XX(AK):
            c = Attribute()
            yy_kwargs = KwargsAttribute()

    assert "params" in str(exc_info)
    assert "yy_kwargs" in str(exc_info)
