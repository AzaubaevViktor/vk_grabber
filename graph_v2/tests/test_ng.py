import pytest

from core import Attribute
from graph import Model
from graph_v2 import Q


class TModel(Model):
    a = Attribute(uid=True)
    b = Attribute(default=100)
    c = Attribute()


def test_create(nodes):
    q = Q()
    q += Q.create(*nodes)
    q += Q.var('result', Q.find(TModel.query(a=3)))
    q += Q.ret('result')

    result = q.run()

    assert len(result) == 0
    assert isinstance(result[0], TModel)
    assert result[0].id == 3
    assert result[0].b == 100
    assert result[0].c == 20


def test_update_create(nodes):
    q = Q()
    q += Q.update(*nodes)
    q.run()

    p = Q()
    p += Q.var('result', Q.find(TModel))
    p += Q.ret('result')
    results = p.run()
    assert len(results) == len(nodes)
    assert results == nodes


@pytest.mark.parametrize('count', (1, 2))
def test_update_existing(created_nodes, count):
    for i in range(count):
        node = created_nodes[i]
        node.c *= 2

    q = Q()
    q += Q.update(*created_nodes)
    q.run()

    q = Q()
    q += Q.var('result', Q.find(TModel.query()))
    q += Q.ret('result')

    results = q.run()

    assert len(results) == len(created_nodes)

    assert results == created_nodes

    for n, m in zip(results, created_nodes):
        assert n.c == m.c
