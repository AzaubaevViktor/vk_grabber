from typing import Optional

import aiofiles
from aiohttp import web

from core import Log


class MonitoringServer:
    instance: Optional["MonitoringServer"] = None

    def __init__(self, monitor_method, app_info):
        if self.instance:
            raise RuntimeError("Run server only once, please")

        self.__class__.instance = self

        self.log = Log(self.__class__.__name__)
        self.template: str = None
        self.monitor_method = monitor_method
        self.app_info = app_info

    async def hello(self, request):
        return web.Response(body=self.template, content_type="text/html")

    async def monitor(self, request):
        return web.json_response({'status': self.monitor_method()})

    async def info(self, request):
        import git

        repo = git.Repo(search_parent_directories=True)
        sha = repo.head.object.hexsha

        return web.json_response({'version': sha[:6], 'stage': self.app_info.stage})

    async def __call__(self):
        self.log.info("Load templates")
        async with aiofiles.open("core/work/monitor_page.html", mode='rt') as f:
            self.template = await f.read()

        self.log.info("Start web server")

        app = web.Application()

        app.add_routes([
            web.get('/', self.hello),
            web.get('/metrics', self.monitor),
            web.get('/info', self.info)
        ])

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
