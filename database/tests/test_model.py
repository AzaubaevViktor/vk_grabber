import pytest

from database import Model, ModelAttribute


class TModel(Model):
    uid = ModelAttribute(uid=True)
    first = ModelAttribute()
    second = ModelAttribute(default=False)
    third = ModelAttribute(default=100)
    fourth = ModelAttribute(default=None)


def test_create():
    model = TModel(uid=10, first=20)
    assert model.uid == 10
    assert model.first == 20
    assert model.second is False
    assert model.third == 100
    assert model.fourth is None

    assert model.verificate()

    assert model.serialize() == {
        'uid': 10,
        'first': 20,
        'second': False,
        'third': 100,
        'fourth': None
    }

    assert model.query() == {
        'uid': 10,
        'first': 20,
    }

    assert model.updates() == {
        'uid': 10,
        'first': 20,
    }


@pytest.mark.parametrize('uid', (0, False, None, 100, -100, "kafskljasf", '🤔'))
def test_query(uid):
    model = TModel(uid=uid)
    assert model.uid == uid
    assert model.first is None
    assert model.second is False
    assert model.third == 100
    assert model.fourth is None

    with pytest.raises(ValueError):
        model.verificate()

    assert model.serialize() == {
        'uid': uid,
        'second': False,
        'third': 100,
        'fourth': None
    }

    assert model.query() == {
        'uid': uid
    }

    assert model.updates() == {
        'uid': uid
    }


@pytest.mark.parametrize('second', (None, True, False))
@pytest.mark.parametrize('third', (None, -1, 0, 50, 100, 1000))
@pytest.mark.parametrize('fourth', (None, 10, False, True))
def test_default(second, third, fourth):
    kwargs = {}

    if second is not None:
        kwargs['second'] = second
    if third is not None:
        kwargs['third'] = third
    if fourth is not None:
        kwargs['fourth'] = fourth

    model = TModel(uid=10, first=20, **kwargs)
    assert model.uid == 10
    assert model.first == 20

    if second is not None:
        assert model.second is second
    if third is not None:
        assert model.third == 100
    if fourth is not None:
        assert model.fourth == fourth

    with pytest.raises(ValueError):
        model.verificate()

    assert model.serialize() == {
        'uid': 10,
        'first': 20,
        'second': False if (second is None) else second,
        'third': 100 if (third is None) else third,
        'fourth': None if (fourth is None) else fourth
    }

    q = {
        'uid': 10,
        'second': True
    }

    if second is not None:
        q['second'] = second
    if third is not None:
        q['third'] = third
    if fourth is not None:
        q['fourth'] = fourth

    assert model.query() == q
    assert model.updates() == q


def test_updates():
    item = TModel(uid=1)

    item.updates() == {'uid': 1}
    item.drop_updates()
    assert item.updates() == {}

    item.first = 100
    item.second = 200

    assert item.updates() == {'first': 100, 'second': 200}
    item.drop_updates()
    assert item.updates() == {}

