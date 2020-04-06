from core import Attribute, AttributeStorage


class Check(AttributeStorage):
    param = Attribute()
    checked: bool = Attribute(default=False)


def test_insert_search(collection):
    collection.insert_many([
        dict(Check(param=i)) for i in range(10)
    ])

    uids = []

    for item_raw in collection.find({'checked': False}):
        del item_raw['_id']
        item = Check(**item_raw)

        assert not item.checked
        uids.append(item.param)

    assert len(set(uids)) == 10
