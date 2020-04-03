import pytest


@pytest.fixture(scope='session')
def driver():
    from neo4j import GraphDatabase

    driver = GraphDatabase.driver(
        "bolt://localhost:7687",
        auth=("neo4j", "test"),
        database="test"
    )
    print(driver)
    print(type(driver))
    print(type(driver).__mro__)
    yield driver

    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        results = session.run("MATCH (n)")

    assert not results
