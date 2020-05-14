import asyncio
from time import time

import pytest

from core.monitor import Monitoring, ListPage, DictPage, PageAttribute

pytestmark = pytest.mark.asyncio


class MainListPage(ListPage):
    MAX_SIZE = 10
    pass


class RequestPage(DictPage):
    date = PageAttribute()
    method = PageAttribute()
    url = PageAttribute()


@pytest.mark.monitor_server
async def test_index(config, mon: Monitoring):
    mon.list_page = MainListPage("_list", "List page")

    def md(request, handler):
        mon.list_page.append(RequestPage(
            id=f"request_{time()}",
            name=f"Request {time()}",
            date=time(),
            method=request.method,
            url=str(request.url)
        ))

    mon.add_page(mon.list_page)
    mon.add_middleware(md)

    print("Connect:")

    print(f"http://{mon.addr}:{mon.port}/")

    await asyncio.sleep(3600)
