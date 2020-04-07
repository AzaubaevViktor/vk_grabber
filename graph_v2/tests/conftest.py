import pytest

from graph_v2 import Q
from graph_v2.tests.test_ng import TModel


@pytest.fixture(scope='session')
def _driver():
    from neo4j import GraphDatabase

    # TODO: Use test config

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "test"),
        database="test"
    )
    print(driver)
    print(type(driver))
    print(type(driver).__mro__)

    return driver


@pytest.fixture(scope='session')
def Q_connect(_driver):
    Q.connect(_driver)

    yield

    Q.cleanup()

    with _driver.session() as session:
        results = session.run("MATCH (n)")

    assert not tuple(results.records())


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