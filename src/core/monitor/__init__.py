"""
Модуль, реализующий веб-интрефейс и консоль управления.
"""

from time import time
from typing import Dict

import aiofiles
from aiohttp import web
from aiohttp.web_request import Request

from core import Log, Time, Attribute
from .page import DictPage, PageAttribute, BasePage, ListPage


class MainPage(DictPage):
    """Главная страница с основными характеристиками приложения"""
    info = PageAttribute()
    start_time = Attribute()
    queries = PageAttribute(default=0)

    @PageAttribute.property
    def work_time(self):
        return str(Time(self.start_time, ago=True))


# TODO: Add server class
class Monitoring:
    """Класс веб-сервера"""
    API_PATH = "/api"

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.log = Log(f"Monitoring")
        self._pages: Dict[str, BasePage] = {}

        self.main_page = MainPage("_main", "Info")
        self.add_page(self.main_page)

        self.app: web.Application = None

        self._middleware = []

    def __getitem__(self, item: str) -> BasePage:
        """Возвращает страницу"""
        return self._pages[item]

    def __getattr__(self, item):
        try:
            return super().__getattr__(item)
        except AttributeError:
            return self._pages[item]

    def add_page(self, page: BasePage):
        assert page.id not in self._pages
        self._pages[page.id] = page

    def add_middleware(self, func):
        self._middleware.append(func)

    async def warm_up(self):
        self.log.info("Running", addr=self.addr, port=self.port)
        self.log.important("You can access to monitoring by",
                           addr=f"http://{self.addr}:{self.port}/")

        self.app = web.Application(middlewares=[self.error_middleware])

        self.app.add_routes([
            web.get(f"/", self._get_index),
            web.get(f"{self.API_PATH}/ping", self._get_ping),
            web.get(f"{self.API_PATH}/pages", self._get_pages),
            web.get(f"{self.API_PATH}/page/{{id}}", self._get_page),
        ])

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)

        await site.start()
        self.log.info("Server started")
        self.main_page.start_time = time()

    async def shutdown(self):
        self.log.info("Server shutdown")
        await self.runner.shutdown()
        self.log.info("Server cleanup")
        await self.runner.cleanup()
        self.log.info("Server gracefully stopped")

    async def _get_index(self, request):
        async with aiofiles.open("core/monitor/app.html", mode='rt') as f:
            template = await f.read()

        return web.Response(body=template, content_type="text/html")

    async def _get_ping(self, request):
        return web.json_response({'status': 'ok',
                                  'time': time()})

    async def _get_pages(self, request):
        answer_ = []

        for page in self._pages.values():
            answer_.append(page.page_info())

        return web.json_response(answer_)

    async def _get_page(self, request):
        page_id = request.match_info['id']

        # TODO: NotFoundPage
        page = self._pages[page_id]

        return web.json_response(page.to_dict())

    @web.middleware
    async def error_middleware(self, request: Request, handler):
        try:
            for md in self._middleware:
                md(request, handler)

            self.main_page.queries += 1

            response = await handler(request)

            if response.status == 200:
                return response

            message = response.message
        except web.HTTPException as ex:
            self.log.exception(request=request, handler=handler)

            if ex.status != 404:
                raise
            message = ex.reason
        except Exception as e:
            self.log.exception(request=request, handler=handler)
            message = str(e)

        return web.json_response({'status': 'error',
                                  'message': message})

