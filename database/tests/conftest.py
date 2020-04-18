import asyncio

import pytest
import motor.motor_asyncio

from core import Log
from database import DBWrapper


@pytest.yield_fixture(scope='session')
def event_loop(request):
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope='session')
def log():
    return Log("db_test")


@pytest.fixture(scope='session')
async def client(config, log):
    client = motor.motor_asyncio.AsyncIOMotorClient(config.mongo.uri)
    log.info("Try to conenct to mongo server")
    log.info("Connection info", await client.server_info())

    yield client

    client.close()


@pytest.fixture(scope='function')
async def db(client, config):
    db = DBWrapper(client, config.mongo.database)
    yield db
    await db.delete_all(i_understand_delete_all=True)
