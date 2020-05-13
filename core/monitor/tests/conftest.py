from time import time

import aiohttp
import pytest

from core import Log
from core.monitor import Monitoring


class MonitoringTestApi:
    def __init__(self, monitoring: Monitoring):
        self.mon = monitoring
        self.log = Log("MonitoringAPI")
        self.log.important(monitoring=monitoring)

        # noinspection PyTypeChecker
        self.session: aiohttp.ClientSession = "Call .warm_up() please"

    async def warm_up(self):
        self.session = aiohttp.ClientSession()

    async def shutdown(self):
        await self.session.close()
        del self.session

    def _url(self, sub: str):
        assert not sub.startswith('/')
        return f"http://{self.mon.addr}:{self.mon.port}{self.mon.API_PATH}/{sub}"

    async def ping(self):
        self.log.info("Send ping")

        start_ = time()
        url = self._url('ping')
        self.log.debug(url=url)
        async with self.session.get(url) as resp:
            assert resp.status == 200
            self.log.info(await resp.json())
            finish_ = time()

        self.log.info("Recv pong", time_=finish_ - start_)

        return finish_ - start_


@pytest.fixture(scope='function')
async def mon() -> Monitoring:
    conn = ('localhost', 9876)
    monitoring = Monitoring(*conn)

    await monitoring.warm_up()

    yield monitoring

    await monitoring.shutdown()

    # TODO: Check monitoring shutdowns


@pytest.fixture(scope='function')
async def conn(mon: Monitoring) -> MonitoringTestApi:
    conn_ = MonitoringTestApi(mon)
    await conn_.warm_up()
    yield conn_
    await conn_.shutdown()
