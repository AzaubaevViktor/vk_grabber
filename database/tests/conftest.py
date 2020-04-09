import pytest
import motor.motor_asyncio

from database import Model


class DBWrapper:
    def __init__(self, db):
        self.db = db

    async def insert_many(self, *objs: Model):
        raise NotImplementedError()

    async def find(self, obj):
        raise NotImplementedError()

    async def find_one(self, obj):
        raise NotImplementedError()

    async def update(self, obj):
        raise NotImplementedError()


@pytest.fixture(scope='session')
def db():
    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')
    dyploma_db = client['dyploma']
    return dyploma_db


# @pytest.fixture(scope='session')
# def collection(db):
#     coll = db['test']
#     yield coll
#     coll.delete_many({})
