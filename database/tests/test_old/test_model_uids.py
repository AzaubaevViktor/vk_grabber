from database import Model, ModelAttribute


class TUids(Model):
    one_uid = ModelAttribute(uid=True)
    two_uid = ModelAttribute(uid=True)

    no_uid = ModelAttribute()


def test_model_uids():
    obj = TUids(two_uid=10, no_uid=20)

    assert obj._id == obj.two_uid == obj.one_uid == 10

    assert obj.verificate()
    assert obj.serialize() == {
        '_id': 10,
        'no_uid': 20
    }

    assert obj.updates() == {
        '_id': 10,
        'no_uid': 20
    }


def test_model_uids_update():
    obj = TUids(_id=10, no_uid=20)

    assert obj.serialize() == {
        '_id': 10,
        'no_uid': 20
    }

    assert obj.updates() == {
        '_id': 10,
        'no_uid': 20
    }

    obj.two_uid = 30

    assert obj._id == 30

    assert obj.serialize() == {
        '_id': 30,
        'no_uid': 20
    }

    assert obj.updates() == {
        '_id': 30,
        'no_uid': 20
    }
