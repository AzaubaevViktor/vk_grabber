import pytest
from neo4j import Driver

from core import AttributeStorage, Attribute
from graph import Link, create_node, find_nodes, do_links, find_links


class TModel(AttributeStorage):
    uid = Attribute(uid=True)
    name: str = Attribute()
    value: int = Attribute()


class TModelChild(AttributeStorage):
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


def test_create_update(driver):
    node = TModel.dummy(uid=30)
    assert isinstance(node, Dummy)
    assert isinstance(node, TModel)

    with driver.session() as session:
        session.write_transaction(create_node, node)

    new_node = TModel(uid=30, name='test', value=123)

    assert node.uid == new_node.uid

    with driver.session() as session:
        session.write_transaction(update_node, new_node)
        result = session.read_transaction(find_nodes, TModel, uid=new_node.uid)

    assert result == new_node
