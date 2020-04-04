import webbrowser
from asyncio import Event
from random import randint

import aiofiles
from aiohttp import web
from aiohttp.abc import BaseRequest

from core import Log


class RedirectServer:
    def __init__(self):
        self.log = Log("RedirectServer")

        self.app: web.Application = None
        self.runner: web.AppRunner = None
        self.site: web.TCPSite = None
        self.template: str = None

        self.data = None
        self.data_received = Event()

        self.address = "localhost"
        self.port = randint(8081, 9000)

    @property
    def redirect_address(self):
        return f"{self.address}:{self.port}/redirect"

    async def warm_up(self):
        async with aiofiles.open("vk_utils/redirect_page.html", mode='rt') as f:
            self.template = await f.read()

        self.app = web.Application()
        self.app.add_routes([
            web.get('/redirect', self._handler_get),
            web.post('/redirect', self._handler_post)
        ])

        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.address, self.port)
        self.log.info("Start redirect server")
        await self.site.start()

    async def _handler_get(self, request: BaseRequest):
        return web.Response(body=self.template, content_type="text/html")

    async def _handler_post(self, request: BaseRequest):
        path = (await request.json())['answer']
        self.data = dict(item.split('=') for item in path.split("&"))
        self.data_received.set()
        return web.json_response({'status': 'ok'})

    async def __call__(self):
        await self.data_received.wait()
        self.log.info("Data received!")
        return self.data

    async def __aenter__(self):
        await self.warm_up()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.log.info("Stopping WebServer")
        await self.site.stop()
        await self.runner.cleanup()
        await self.app.cleanup()
        self.log.info("WebServer stopped")


class UpdateToken:
    def __init__(self, config_vk):
        self.log = Log("UpdateToken")

        self.config = config_vk
        self.client_id = self.config.client_id
        self.finished = Event()

    async def __call__(self) -> str:
        async with RedirectServer() as server:
            redirect_address = server.redirect_address

            url = "https://oauth.vk.com/authorize" \
                  f"?client_id={self.client_id}" \
                  "&display=page" \
                  f"&redirect_uri={redirect_address}" \
                  "&scope=friends,wall,offline,groups" \
                  "&response_type=token" \
                  "&v=5.103"

            webbrowser.open_new(url)

            data = await server()

            self.config.token = data['access_token']
            self.config.user_id = data['user_id']

            self.config.update()
            self.log.info("Token updated")

        self.finished.set()
