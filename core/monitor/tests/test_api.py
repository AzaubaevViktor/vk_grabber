import pytest

from core.monitor import Monitoring, DictPage, PageAttribute, ListPage
from core.monitor.tests.conftest import MonitoringTestApi

pytestmark = pytest.mark.asyncio


async def test_run(conn: MonitoringTestApi):
    assert await conn.ping()


async def test_default_page(conn: MonitoringTestApi):
    pages = await conn.pages()
    assert len(pages) == 1

    page_data = await conn.page('_main')
    assert page_data['name']
    assert page_data['id'] == '_main'
    assert page_data['template'] == 'dict'


class EmptyPage(DictPage):
    pass


async def test_add_page(conn: MonitoringTestApi, mon: Monitoring):
    page_name = "Test Empty Dict page"
    page_id = "test_empty"

    page = EmptyPage(page_id, page_name)
    await mon.add_page(page)

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
    await mon.add_page(page)

    pages = await conn.pages()
    assert len(pages) == 2

    page_data = await conn.page(page_id)
    assert page_data['name'] == page_name
    assert page_data['id'] == page_id
    assert page_data['template'] == 'dict'
    assert page_data['data'] == {
        'a': None,
        'b': None
    }

    page.a = 10
    page_data = await conn.page(page_id)
    assert page_data['data'] == {
        'a': 10,
        'b': None
    }

    page.b = "Hello, world!"
    page_data = await conn.page(page_id)
    assert page_data['data'] == {
        'a': 10,
        'b': "Hello, world!"
    }


class ListPageTest(ListPage):
    pass


async def test_list_page(conn: MonitoringTestApi, mon: Monitoring):
    page_name = "Test List page"
    page_id = "test_list"

    page = ListPageTest(page_id, page_name)
    await mon.add_page(page)

    pages = await conn.pages()
    assert len(pages) == 2

    page_data = await conn.page(page_id)
    assert page_data['name'] == page_name
    assert page_data['id'] == page_id
    assert page_data['template'] == 'dict'
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
    assert sub_page_data['data'] == {
        'a': None,
        'b': None
    }

    # sub page with attr a
    sub_page.a = 'Check'

    page_data = await conn.page(page_id)
    assert isinstance(page_data['data'], list)
    assert len(page_data['data']) == 1
    sub_page_data = page_data['data'][0]
    assert sub_page_data['data'] == {
        'a': 'Check',
        'b': None
    }

    # sub page with attr a and b
    sub_page.b = 1.2

    page_data = await conn.page(page_id)
    assert isinstance(page_data['data'], list)
    assert len(page_data['data']) == 1
    sub_page_data = page_data['data'][0]
    assert sub_page_data['data'] == {
        'a': 'Check',
        'b': 1.2
    }
