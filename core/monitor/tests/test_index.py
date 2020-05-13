import asyncio

import pytest

from core.monitor import Monitoring

pytestmark = pytest.mark.asyncio


@pytest.mark.monitor_server
async def test_index(config, mon: Monitoring):
    print("Connect:")

    print(f"http://{mon.addr}:{mon.port}/")

    await asyncio.sleep(3600)
