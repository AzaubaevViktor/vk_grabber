import pytest

from core import AttributeStorage, Attribute, KwargsAttribute


class XXX(AttributeStorage):
    uid = Attribute(uid=True)
    value = Attribute()


def test_uids():
    assert XXX.uid.uid
    assert not XXX.value.uid

    assert XXX.uid in XXX.__uids__.values()
    assert XXX.value not in XXX.__uids__.values()


def test_wrong():
    with pytest.raises(AttributeError):
        class Wrong(AttributeStorage):
            kwargs = KwargsAttribute(uid=True)


class YYY(XXX):
    pass


def test_uids_inh():
    assert YYY.uid.uid
    assert YYY.uid in YYY.__uids__.values()


class ZZZ(XXX):
    uid = Attribute(uid=True)


def test_double_uids():
    assert len(ZZZ.__uids__) == 1
    assert ZZZ.uid in ZZZ.__uids__.values()
    assert XXX.uid not in ZZZ.__uids__.values()
