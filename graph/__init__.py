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


def _q_attrs_from(name, node_atts):
    keys = "{" + ', '.join(f"{attr_name}:${name}_{attr_name}" for attr_name in node_atts.keys()) + "}"
    kwargs = {f'{name}_{attr_name}': attr_value
              for attr_name, attr_value in node_atts.items()}
    return keys, kwargs


def _q_create_node(node: Model, name: str):
    node_atts = dict(node)

    keys, kwargs = _q_attrs_from(name, node_atts)

    return f"CREATE ({name}:{node.labels()} {keys})\n", kwargs


def _q_match(model: Type[Model], uid, name, **attrs) -> Tuple[str, dict]:
    query = f"MATCH ({name}:{model.labels()} "

    if uid:
        assert model.__uids__, ("Set uid Attribute for", model)
        if len(model.__uids__) != 1:
            raise NotImplementedError()

        uid_field = tuple(model.__uids__.values())[0]

        attrs[uid_field.name] = uid

    if attrs:
        q_, kwargs = _q_attrs_from(name, attrs)
        query += q_
    else:
        kwargs = {}

    query += ")\n"

    return query, kwargs


def find_nodes(tx, model: Type[Model], uid=None, limit=None, **attrs):
    # TODO: Add custom attributes return
    items = []

    query, attrs = _q_match(model, uid, 'result', **attrs)

    query += "RETURN result\n"

    if limit:
        query += f"LIMIT {limit}"

    for item in tx.run(query, **attrs):
        result: Node = item['result']

        assert model.__name__ in result.labels

        if "Dummy" in result.labels:
            used_model = model.Dummy()
        else:
            used_model = model

        items.append(used_model(
            **result
        ))

    print(query)

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

    query = f"MERGE ({name}:{node.labels()} {{{uid_field.name}:$_{name}_uid_value}}) "

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

    tx.run(query, **kwargs)


def find_links(tx, node: Model, link: Link, model: Type[Model]):
    uid_field, uid_value = _q_get_uid_from_node(node)

    query, kwargs = _q_match(node.__class__, uid_value, "parent")
    query += f"MATCH (parent)-[:{link.labels()}]->(node:{model.labels()})\n"
    query += "RETURN node"

    items = []

    for item in tx.run(query, **kwargs):
        result: Node = item['node']
        assert model.__name__ in result.labels

        items.append(model(**result))

    return items


def update_node(tx, node: Model):
    q, kwargs = _q_merge(node, "result", on_create=True, on_match=True)

    q += "REMOVE result:Dummy\n"

    tx.run(q, **kwargs)


__all__ = ("create_nodes",)