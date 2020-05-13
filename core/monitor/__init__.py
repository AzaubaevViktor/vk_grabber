from time import time

from aiohttp import web
from aiohttp.web_request import Request

from core import Log
from .page import DictPage, PageAttribute


class MainPage(DictPage):
    info = PageAttribute()


class Monitoring:
    API_PATH = "/api"

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.log = Log(f"Monitoring")
        self._pages = [
            MainPage("_main", "Info")
        ]

    async def warm_up(self):
        self.log.important("Running", addr=self.addr, port=self.port)

        app = web.Application(middlewares=[self.error_middleware])

        app.add_routes([
            web.get(f"{self.API_PATH}/ping", self._get_ping),
            web.get(f"{self.API_PATH}/pages", self._get_pages),
            web.get(f"{self.API_PATH}/page/{{id}}", self._get_page),
        ])

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, self.addr, self.port)

        await site.start()
        self.log.info("Server started")

    async def shutdown(self):
        self.log.info("Server shutdown")
        await self.runner.shutdown()
        self.log.info("Server cleanup")
        await self.runner.cleanup()
        self.log.info("Server gracefully stopped")

    async def _get_ping(self, request):
        return web.json_response({'status': 'ok',
                                  'time': time()})

    async def _get_pages(self, request):
        answer_ = []

        for page in self._pages:
            answer_.append(page.to_dict())

        return web.json_response(answer_)

    async def _get_page(self, request):
        page_id = request.match_info['name']

        raise NotImplementedError()

    @web.middleware
    async def error_middleware(self, request: Request, handler):
        try:
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

