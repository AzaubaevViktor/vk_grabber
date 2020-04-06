import pytest
from pymongo import MongoClient


@pytest.fixture(scope='session')
def db():
    client = MongoClient('mongodb://root:root@localhost:27017/')
    dyploma_db = client['dyploma']
    return dyploma_db


@pytest.fixture(scope='session')
def collection(db):
    coll = db['test']
    yield coll
    coll.delete_many({})
