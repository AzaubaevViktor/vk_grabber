import pytest

from graph_v2.tests.test_ng import TModel


@pytest.fixture(scope='function')
def nodes():
    nodes = []
    nodes.append(TModel(a=1, c=10))
    nodes.append(TModel(a=2, b=50, c=10))
    nodes.append(TModel(a=3, c=20))
    nodes.append(TModel(a=4, b=150, c=30))
    nodes.append(TModel(a=5, c=40))

    return nodes


@pytest.fixture(scope='function')
def created_nodes(nodes):
    q = Q()
    q += Q.create(*nodes)

    q.run()

    return nodes