import pytest

from core import Attribute
from graph import Model
from graph_v2 import Q


class FullModel(Model):
    uid = Attribute(uid=True)
    param = Attribute(default=100)
    value = Attribute()


@pytest.fixture(scope='function')
def dummy_model():
    q = Q()
    q += Q.create(FullModel.dummy(uid=10))

    q.run()

    q = Q()
    q += Q.var('result', Q.find(FullModel.Dummy().query()))
    q += Q.ret('result')

    results = q.run()
    assert len(results) == 1
    assert isinstance(results[0], FullModel.Dummy())
    assert isinstance(results[0], FullModel)

    return 10


def test_update_dummy(dummy_model):
    q = Q()
    q += Q.update(FullModel(uid=dummy_model, value=500))
    q.run()

    q = Q()
    q.var('result', Q.find(FullModel.query(uid=dummy_model)))
    q.ret('result')

    results = q.run()

    assert len(results) == 1

    result = results[0]
    assert isinstance(result, FullModel)
    assert not isinstance(result, FullModel.Dummy())
