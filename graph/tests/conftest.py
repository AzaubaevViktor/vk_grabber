import pytest


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


@pytest.fixture(scope='function')
def driver(_driver):
    yield _driver

    with _driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        results = session.run("MATCH (n)")

    assert not tuple(results.records())
