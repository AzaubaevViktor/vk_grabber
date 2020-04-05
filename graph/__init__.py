from typing import Sequence, Tuple

from neo4j.graph import Node

from typing import Type
from .link import Link
from .model import Model


def create_nodes(tx, *nodes: Model):
    q, kwargs = "", {}

    for i, node in enumerate(nodes):
        q_, kwargs_ = _q_create_node(node, f"node_{i}")
        q += q_
        kwargs.update(kwargs_)

    tx.run(q, **kwargs)


def _q_create_node(node: Model, name: str):
    node_atts = dict(node)

    keys = "{" + ', '.join(f"{attr_name}:${name}_{attr_name}" for attr_name in node_atts.keys()) + "}"

    kwargs = {f'{name}_{attr_name}': attr_value
              for attr_name, attr_value in node_atts.items()}

    return f"CREATE ({name}:{node.labels()} {keys})\n", kwargs


def _q_match(model: Type[Model], uid, name) -> Tuple[str, dict]:
    assert model.__uids__, "Set uid Attribute"
    if len(model.__uids__) != 1:
        raise NotImplementedError()

    uid_field = tuple(model.__uids__.values())[0]

    return f"MATCH ({name}:{model.labels()} {{{uid_field.name}: ${name}_uid_value}})\n", {
        f'{name}_uid_value': uid
    }


def find_nodes(tx, model: Type[Model], uid=None):
    items = []

    query, kwargs = _q_match(model, uid, 'result')

    for item in tx.run(f"{query} RETURN result",
                       **kwargs
                       ):
        result: Node = item['result']

        assert model.__name__ in result.labels

        items.append(model(
            **result
        ))

    return items


def _q_get_uid_from_node(node: Model):
    assert node.__uids__, "Set uid Attribute"
    if len(node.__uids__) != 1:
        raise NotImplementedError()

    uid_field = tuple(node.__uids__.values())[0]

    return uid_field, getattr(node, uid_field.name)


def _q_merge(node: Model, name: str, on_create=True, on_match=False):
    uid_field, uid_value = _q_get_uid_from_node(node)

    kwargs = {f'_{name}_uid_value': uid_value}

    query = f"MERGE ({name}:{node.__class__.__name__} {{{uid_field.name}:$_{name}_uid_value}}) "

    if on_create or on_match:
        params = []

        for k, v in dict(node).items():
            params.append(f"{name}.{k} = ${name}_{k}")
            kwargs[f"{name}_{k}"] = v
        _q = ", ".join(params)

        if on_create:
            query += f"ON CREATE SET {_q}\n"
        if on_match:
            query += f"ON MATCH SET {_q}\n"
    print(query)
    return query, kwargs


def do_links(tx, node: Model, link: Link, nodes: Sequence[Model]):
    query = ""
    kwargs = {}

    q, k = _q_merge(node, "parent")
    query += q
    kwargs.update(k)

    for i, item in enumerate(nodes):
        name = f"child_{i}"
        q, k = _q_merge(item, name)
        query += q
        kwargs.update(k)

        query += f"MERGE (parent)-[:{link.labels()}]->({name})\n"
    print(query, kwargs)
    tx.run(query, **kwargs)


def find_links(tx, node: Model, link: Link, model: Type[Model]):
    uid_field, uid_value = _q_get_uid_from_node(node)

    query, kwargs = _q_match(node.__class__, uid_value, "parent")
    query += f"MATCH (parent)-[:{link.labels()}]->(node:{model.labels()})\n"
    query += "RETURN node"

    print(query, kwargs)

    items = []

    for item in tx.run(query, **kwargs):
        result: Node = item['node']
        assert model.__name__ in result.labels

        items.append(model(**result))

    return items


def update_node(tx, node: Model):
    q, kwargs = _q_merge(node, "result", on_create=True, on_match=True)

    if node.__class__.__mro__[0].__name__ == "Dummy":
        q += "REMOVE result:Dummy\n"

    tx.run(q, **kwargs)


__all__ = ("create_nodes",)