import asyncio
from time import time

import pytest

from core.monitor import Monitoring, ListPage, DictPage, PageAttribute

pytestmark = pytest.mark.asyncio


class ListRequestPage(ListPage):
    MAX_SIZE = 10
    pass


class RequestPage(DictPage):
    date = PageAttribute()
    method = PageAttribute()
    url = PageAttribute()


@pytest.fixture(scope='function')
async def sorted_test_page():
    class MyPage(DictPage):
        sorted_value = PageAttribute()
        created_time = PageAttribute()

    class SortedTestPage(ListPage):
        MAX_SIZE = 10

        def sorted_function(self, item: MyPage):
            return item.sorted_value

    page = SortedTestPage('_sort', "Sorted values")

    async def worker():
        from random import randint
        while True:
            rnd_value = randint(0, 100)
            page.append(MyPage(
                id=rnd_value,
                name=f"Test page {rnd_value}",
                sorted_value=rnd_value,
                created_time=time()
            ))
            await asyncio.sleep(1)

    task = asyncio.create_task(worker())

    yield page

    await task


# @pytest.mark.skip
@pytest.mark.monitor_server
async def test_index(config, mon: Monitoring, sorted_test_page):
    mon.list_page = ListRequestPage("_list", "List page")
    mon.sorted_page = sorted_test_page

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

    mon.add_page(mon.sorted_page)

    print("Connect:")

    print(f"http://{mon.addr}:{mon.port}/")

    await asyncio.sleep(3600)
