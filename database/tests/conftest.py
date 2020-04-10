import asyncio

import pytest
import motor.motor_asyncio

from database import DBWrapper


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
async def client(config):
    return motor.motor_asyncio.AsyncIOMotorClient(config.mongo.uri)


@pytest.fixture(scope='function')
async def db(client, config):
    db = DBWrapper(client, config.mongo.database)
    yield db
    await db.delete_all(i_understand_delete_all=True)
