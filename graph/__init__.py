from neo4j.graph import Node

from core import AttributeStorage, Type


class Link:
    LTR = None

    pass


def create_node(tx, node: AttributeStorage):
    des = dict(node)

    keys = "{" + ', '.join(f"{name}:${name}" for name in des.keys()) + "}"

    tx.run(f"CREATE (:{node.__class__.__name__} {keys})",
           **des
           )


def find_nodes(tx, model: Type[AttributeStorage], uid):
    assert model.__uids__, "Set uid Attribute"
    if len(model.__uids__) != 1:
        raise NotImplementedError()

    uid_field = model.__uids__[0]

    items = []

    for item in tx.run(f"MATCH (result:{model.__name__} {{{uid_field.name}: $uid_value}}) RETURN result",
                       uid_value=uid
                       ):
        result: Node = item['result']

        assert model.__name__ in result.labels

        items.append(model(
            **result
        ))

    return items
