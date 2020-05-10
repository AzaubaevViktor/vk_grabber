from database import Model


class A(Model):
    pass


class B(Model):
    COLLECTION = "A"


class C(Model):
    pass


def test_collection(db):
    assert db.get_collection(A) == db.get_collection(A)
    assert db.get_collection(A) == db.get_collection(B)
    assert db.get_collection(A) != db.get_collection(C)

    assert db.get_collection(B) == db.get_collection(A)
    assert db.get_collection(B) == db.get_collection(B)
    assert db.get_collection(B) != db.get_collection(C)

    assert db.get_collection(C) != db.get_collection(A)
    assert db.get_collection(C) != db.get_collection(B)
    assert db.get_collection(C) == db.get_collection(C)