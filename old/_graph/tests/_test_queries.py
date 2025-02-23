import pytest
from neo4j import Driver

from core import Attribute
from graph import Link, create_nodes, find_nodes, do_links, find_links, Model, update_node


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
        session.write_transaction(create_nodes, node)
        found_node = session.read_transaction(find_nodes, TModel, node.uid)

    assert isinstance(node, TModel)
    assert [node] == found_node


@pytest.mark.parametrize(
    'id_started, name_fmt', ((200, 'test_{}'),
                             (300, 'test+{}'),
                             (400, '/23_1:+-/+{}'))
)
def test_create_nodes(driver: Driver, id_started, name_fmt):
    nodes = []
    for i in range(10):
        nodes.append(TModel(uid=i + id_started, name=name_fmt.format(i), value=123 * i))

    with driver.session() as session:
        session.write_transaction(create_nodes, *nodes)
        found_nodes = session.read_transaction(find_nodes, TModel, nodes[0].uid)

    assert len(found_nodes) == 1

    assert isinstance(found_nodes[0], TModel)
    assert nodes[:1] == found_nodes

    with driver.session() as session:
        found_nodes = session.read_transaction(find_nodes, TModel)

    assert len(found_nodes)

    for item in found_nodes:
        assert isinstance(item, TModel)


@pytest.mark.parametrize("create", (True, False))
def test_create_with_link(driver, create):
    node = TModel(uid=20, name='tost', value=123)
    node_childs = []

    for i in range(10):
        node_childs.append(TModelChild(id=i, some='value'))

    with driver.session() as session:
        session.write_transaction(create_nodes, node)
        if create:
            session.write_transaction(create_nodes, *node_childs)

        session.write_transaction(do_links, node, TLink(param=1), node_childs)
        result = session.read_transaction(find_links, node, TLink(), TModelChild)
        parent = session.read_transaction(find_nodes, TModel)

    assert sorted(result, key=lambda item: item.id) == node_childs
    for node_child in result:
        assert isinstance(node_child, TModelChild)
        assert node_child.some == 'value'

    assert len(parent) == 1
    assert parent == [node]


def test_update(driver):
    node = TModel(uid=15, name="One", value=1)

    with driver.session() as session:
        session.write_transaction(create_nodes, node)

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
        session.write_transaction(create_nodes, dummy_node)

    with driver.session() as session:
        found_dummy_nodes = session.read_transaction(find_nodes, TModel.Dummy(), dummy_node.uid)

    assert len(found_dummy_nodes) == 1

    assert isinstance(found_dummy_nodes[0], TModel.Dummy())

    with driver.session() as session:
        found_dummy_nodes_by_raw = session.read_transaction(find_nodes, TModel, dummy_node.uid)

    assert len(found_dummy_nodes_by_raw) == 1

    assert isinstance(found_dummy_nodes_by_raw[0], TModel.Dummy())

    new_node = TModel(uid=30, name='test', value=123)

    assert dummy_node.uid == new_node.uid

    with driver.session() as session:
        session.write_transaction(update_node, new_node)
        result = session.read_transaction(find_nodes, TModel, uid=new_node.uid)

    assert result == [new_node]

    result = result[0]
    assert isinstance(result, TModel)
    assert not isinstance(result, TModel.Dummy())


@pytest.mark.parametrize('childs_count', (3, 5, 9, 10))
def test_update_do_link(driver, childs_count):
    parent = TModel(uid=1, name='test', value=123)

    node_childs = [
        TModelChild(id=i, some=f'value{i}')
        for i in range(10)
    ]

    with driver.session() as session:
        session.write_transaction(create_nodes, parent)

    # Update
    new_parent = TModel(uid=parent.uid, name='nnew name', value=456)

    with driver.session() as session:
        session.write_transaction(update_node, new_parent)

    # Do links
    with driver.session() as session:
        session.write_transaction(do_links, parent, TLink(), node_childs[:childs_count])

    # check

    with driver.session() as session:
        parents = session.read_transaction(find_nodes, TModel, parent.uid)
        childs = session.read_transaction(find_links, parent, TLink(), TModelChild)

    assert len(parents) == 1
    assert new_parent == parents[0]

    assert len(childs) == childs_count
    assert sorted(childs, key=lambda item: item.id) == node_childs[:childs_count]

