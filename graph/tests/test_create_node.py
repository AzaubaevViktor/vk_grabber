import pytest
from neo4j import Driver

from core import Attribute
from graph import Link, create_node, find_nodes, do_links, find_links, Model


class TModel(Model):
    uid = Attribute(uid=True)
    name: str = Attribute()
    value: int = Attribute()


class TModelChild(Model):
    id = Attribute(uid=True)
    some = Attribute()


class TLink(Link):
    direction = Link.LTR
    param = Attribute(default=None)


def test_create(driver: Driver):
    node = TModel(uid=10, name='test', value=123)
    with driver.session() as session:
        session.write_transaction(create_node, node)
        found_node = session.read_transaction(find_nodes, TModel, node.uid)

    assert isinstance(node, TModel)
    assert [node] == found_node


@pytest.mark.parametrize("create", (True, False))
def test_create_with_link(driver, create):
    node = TModel(uid=20, name='tost', value=123)
    node_childs = []

    for i in range(10):
        node_childs.append(TModelChild(id=i, some='value'))

    with driver.session() as session:
        if create:
            session.write_transaction(create_node, node)
            for item in node_childs:
                session.write_transaction(create_node, item)

        session.write_transaction(do_links, node, TLink(param=1), node_childs)
        result = session.read_transaction(find_links, node, TLink(), TModelChild)

    assert sorted(result, key=lambda item: item.id) == node_childs


def test_update(driver):
    node = TModel(uid=10, name="One", value=1)

    with driver.session() as session:
        session.write_transaction(create_node, node)

    with driver.session() as session:
        nodes = session.read_transaction(find_nodes, TModel, node.uid)

    assert len(nodes) == 1
    assert nodes[0].name == 'One'
    assert nodes[0].value == 1

    node.name = "Two"
    node.value = 2

    with driver.session() as session:
        session.write_transaction(update_node, node)

    with driver.session() as session:
        nodes = session.read_transaction(find_nodes, TModel, node.uid)

    assert len(nodes) == 1
    assert nodes[0].name == 'Two'
    assert nodes[0].value == 2


def test_create_update(driver):
    dummy_node = TModel.dummy(uid=30)
    assert isinstance(dummy_node, TModel)

    with driver.session() as session:
        session.write_transaction(create_node, dummy_node)

    with driver.session() as session:
        found_dummy_nodes = session.read_transaction(find_nodes, TModel.Dummy(), dummy_node.uid)

    assert len(found_dummy_nodes) == 1

    assert isinstance(found_dummy_nodes[0], TModel)

    new_node = TModel(uid=30, name='test', value=123)

    assert dummy_node.uid == new_node.uid

    with driver.session() as session:
        session.write_transaction(update_node, new_node)
        result = session.read_transaction(find_nodes, TModel, uid=new_node.uid)

    assert result == [new_node]

    result = result[0]
    assert isinstance(result, TModel)
