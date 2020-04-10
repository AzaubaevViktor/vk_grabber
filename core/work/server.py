from aiohttp import web

from core import Log


class MonitoringServer:
    def __init__(self):
        self.log = Log(self.__class__.__name__)

    async def __call__(self):
        self.log.info("Start web server")
        routes = web.RouteTableDef()

        @routes.get('/')
        async def hello(request):
            return web.Response(text="Hello, world")

        app = web.Application()
        app.add_routes(routes)

        self.runner = web.AppRunner(app)
        await self.runner.setup()
        site = web.TCPSite(self.runner, 'localhost', 8080)

        await site.start()
        self.log.info("Site started")

    async def shutdown(self):
        self.log.info("Server shutdown")
        await self.runner.shutdown()
        self.log.info("Server cleanup")
        await self.runner.cleanup()
