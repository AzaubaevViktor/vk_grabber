from time import time

from aiohttp import web

from core import Attribute, AttributeStorage, Log


class Monitoring:
    API_PATH = "/api"

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port
        self.log = Log(f"Monitoring")

    async def warm_up(self):
        self.log.important("Running", addr=self.addr, port=self.port)

        app = web.Application()

        app.add_routes([
            web.get(f"{self.API_PATH}/ping", self._ping)
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

    async def _ping(self, request):
        return web.json_response({'status': 'ok',
                                  'time': time()})

    async def _api_handler(self, request):
        self.log.info(request)

        # TODO: Use exceptions
        return web.json_response({'status': 'fail', 'msg': 'NotImplementedError'})


class PageAttribute(Attribute):
    pass


class BasePage(AttributeStorage):
    TEMPLATE = None


class DictPage(BasePage):
    TEMPLATE = 'dict'


class ListPage(BasePage):
    TEMPLATE = 'list'
