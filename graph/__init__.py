from typing import Sequence, Tuple

from neo4j.graph import Node

from core import AttributeStorage, Type


class Link(AttributeStorage):
    LTR = None


def create_node(tx, node: AttributeStorage):
    des = dict(node)

    keys = "{" + ', '.join(f"{name}:${name}" for name in des.keys()) + "}"

    tx.run(f"CREATE (:{node.__class__.__name__} {keys})",
           **des
           )


def _q_match(model, uid, name) -> Tuple[str, dict]:
    assert model.__uids__, "Set uid Attribute"
    if len(model.__uids__) != 1:
        raise NotImplementedError()

    uid_field = model.__uids__[0]

    return f"MATCH ({name}:{model.__name__} {{{uid_field.name}: ${name}_uid_value}})\n", {
        f'{name}_uid_value': uid
    }


def find_nodes(tx, model: Type[AttributeStorage], uid):
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


def _q_get_uid_from_node(node):
    assert node.__uids__, "Set uid Attribute"
    if len(node.__uids__) != 1:
        raise NotImplementedError()

    uid_field = node.__uids__[0]

    return uid_field, getattr(node, uid_field.name)


def _q_merge_on_create(node, name):
    uid_field, uid_value = _q_get_uid_from_node(node)

    kwargs = {f'_{name}_uid_value': uid_value}

    query = f"MERGE ({name}:{node.__class__.__name__} {{{uid_field.name}:$_{name}_uid_value}}) "

    query += f"ON CREATE SET "

    params = []

    for k, v in dict(node).items():
        params.append(f"{name}.{k} = ${name}_{k}")
        kwargs[f"{name}_{k}"] = v
    query += ", ".join(params) + "\n"

    return query, kwargs


def do_links(tx, node: AttributeStorage, link: Link, nodes: Sequence[AttributeStorage]):
    query = ""
    kwargs = {}

    q, k = _q_merge_on_create(node, "parent")
    query += q
    kwargs.update(k)

    for i, item in enumerate(nodes):
        name = f"child_{i}"
        q, k = _q_merge_on_create(item, name)
        query += q
        kwargs.update(k)

        query += f"MERGE (parent)-[:{link.__class__.__name__.upper()}]->({name})\n"
    print(query, kwargs)
    tx.run(query, **kwargs)


def find_links(tx, node: AttributeStorage, link: Link, model: Type[AttributeStorage]):
    uid_field, uid_value = _q_get_uid_from_node(node)

    query, kwargs = _q_match(node.__class__, uid_value, "parent")
    query += f"MATCH (parent)-[:{link.__class__.__name__.upper()}]->(node:{model.__name__})\n"
    query += "RETURN node"

    print(query, kwargs)

    items = []

    for item in tx.run(query, **kwargs):
        result: Node = item['node']
        assert model.__name__ in result.labels

        items.append(model(**result))

    return items
