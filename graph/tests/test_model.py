from core import Attribute
from graph import Model


class LabelName(Model):
    uid = Attribute(uid=True)
    param_one = Attribute()


def test_one_label():
    assert LabelName.__name__ in LabelName.labels()


class LabelTwo(LabelName):
    x = Attribute()


def test_many_labels():
    assert LabelName.__name__ in LabelTwo.labels()
    assert LabelTwo.__name__ in LabelTwo.labels()


def test_dummy():
    dummy = LabelName.dummy(uid=10)

    assert "Dummy" in dummy.labels()

    assert isinstance(dummy, LabelName)
