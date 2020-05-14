import asyncio

import pytest

from core.monitor import Monitoring
from core.monitor.page import PageAttribute, DictPage, ListPage
from core.monitor.tests.conftest import MonitoringTestApi

pytestmark = pytest.mark.asyncio


async def test_run(conn: MonitoringTestApi):
    try_count = 10

    while try_count:
        try:
            try_count -= 1
            ping_value = await conn.ping()

            assert ping_value
            print(f"{ping_value * 1000:.3}ms")
            return

        except (Exception, AssertionError) as e:
            if not try_count:
                raise e
            print(try_count)
            await asyncio.sleep(1)


async def test_default_page(conn: MonitoringTestApi):
    pages = await conn.pages()
    assert len(pages) == 1

    page_data = await conn.page('_main')
    assert page_data['name']
    assert page_data['id'] == '_main'
    assert page_data['template'] == 'dict'
    assert page_data['work_time'] > 0


class EmptyPage(DictPage):
    pass


async def test_add_page(conn: MonitoringTestApi, mon: Monitoring):
    page_name = "Test Empty Dict page"
    page_id = "test_empty"

    page = EmptyPage(page_id, page_name)
    mon.add_page(page)

    pages = await conn.pages()
    assert len(pages) == 2

    page_data = await conn.page(page_id)
    assert page_data['name'] == page_name
    assert page_data['id'] == page_id
    assert page_data['template'] == 'dict'


class PageWithAttrs(DictPage):
    a = PageAttribute()
    b = PageAttribute()


async def test_attr_page(conn: MonitoringTestApi, mon: Monitoring):
    page_name = "Test Dict page with attrs"
    page_id = "test_attrs"

    page = PageWithAttrs(page_id, page_name)
    mon.add_page(page)

    pages = await conn.pages()
    assert len(pages) == 2

    page_data = await conn.page(page_id)
    assert page_data['name'] == page_name
    assert page_data['id'] == page_id
    assert page_data['template'] == 'dict'
    assert page_data['a'] is None
    assert page_data['b'] is None

    page.a = 10
    page_data = await conn.page(page_id)
    assert page_data['a'] == 10
    assert page_data['b'] is None

    page.b = "Hello, world!"
    page_data = await conn.page(page_id)
    assert page_data['a'] == 10
    assert page_data['b'] == "Hello, world!"


class ListPageTest(ListPage):
    pass


async def test_list_page(conn: MonitoringTestApi, mon: Monitoring):
    page_name = "Test List page"
    page_id = "test_list"

    page = ListPageTest(page_id, page_name)
    mon.add_page(page)

    pages = await conn.pages()
    assert len(pages) == 2

    page_data = await conn.page(page_id)
    assert page_data['name'] == page_name
    assert page_data['id'] == page_id
    assert page_data['template'] == 'list'
    assert page_data['data'] == []

    # SUB PAGE
    sub_page_id = 'sub_page_0'
    sub_page_name = 'Sub item 0'
    sub_page = PageWithAttrs(sub_page_id, sub_page_name)
    page.append(sub_page)

    # empty sub page
    page_data = await conn.page(page_id)
    assert isinstance(page_data['data'], list)
    assert len(page_data['data']) == 1
    sub_page_data = page_data['data'][0]

    assert sub_page_data['name'] == sub_page_name
    assert sub_page_data['id'] == sub_page_id
    assert sub_page_data['template'] == 'dict'
    assert sub_page_data['a'] is None
    assert sub_page_data['b'] is None

    # sub page with attr a
    sub_page.a = 'Check'

    page_data = await conn.page(page_id)
    assert isinstance(page_data['data'], list)
    assert len(page_data['data']) == 1
    sub_page_data = page_data['data'][0]
    assert sub_page_data['a'] == "Check"
    assert sub_page_data['b'] is None

    # sub page with attr a and b
    sub_page.b = 1.2

    page_data = await conn.page(page_id)
    assert isinstance(page_data['data'], list)
    assert len(page_data['data']) == 1
    sub_page_data = page_data['data'][0]
    assert sub_page_data['a'] == 'Check'
    assert sub_page_data['b'] == 1.2
