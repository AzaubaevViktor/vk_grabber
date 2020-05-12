import pytest

from database import Model, ModelAttribute


class A(Model):
    not_uid = ModelAttribute()
    uid = ModelAttribute(uid=True)


def test_uid_uid():
    assert A._id
    assert A._id.name == "_id"

    with pytest.raises(ValueError):
        A._id.name = "not_id_name"

    assert not A._id.is_id_alias

    assert A._id.name not in A.__uids__


def test_uid():
    assert A.uid.is_id_alias
    assert not A.not_uid.is_id_alias

    assert A.not_uid.name not in A.__uids__
    assert A.uid.name in A.__uids__
