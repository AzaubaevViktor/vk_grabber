"""Набор базовых модулей, упрощающих взаимодействие с окружением"""
import motor.motor_asyncio

from core import LoadConfig, Log, BaseWork, CorpinusManager
from core.monitor import Monitoring, ListPage
from database import DBWrapper
from vk_utils import VK


class BaseApplication:
    """Базовое приложение"""
    def __init__(self, config: LoadConfig):
        self.log = Log(self.__class__.__name__)

        self.config = config
        self.ctx = AppContext(self.config)

    async def warm_up(self):
        await self.ctx.warm_up()


class AppContext:
    """Контекст, содержащий в себе необходимые модули"""
    def __init__(self, config: LoadConfig):
        self.config = config
        self.stage_name = config.app.stage
        self.vk = VK(config.vk)
        self.db = DBWrapper(
            motor.motor_asyncio.AsyncIOMotorClient(
                config.mongo.uri
            ),
            config.mongo.database
        )

        self.started_groups = config.vk.groups

        self.posts_count = config.app.posts_count
        self.participants_count = config.app.participants_count

        self.mon = Monitoring(config.monitoring.addr, config.monitoring.port)
        self.mon.add_page(ListPage("works", "Works"))
        self.mon.add_page(ListPage('services', "Services"))

        self.mon.services.append(self.vk.stats)

        self.corpinus = CorpinusManager()
        self.mon.add_page(self.corpinus.page)

    async def warm_up(self):
        await self.mon.warm_up()
        await self.vk.warm_up()


class BaseWorkApp(BaseWork):
    """Базовый сервис с контекстом"""
    def __init__(self, ctx: AppContext):
        super().__init__()
        self.ctx = ctx
        self.db = self.ctx.db
        self.vk: VK = self.ctx.vk

        self.ctx.mon.works.append(self.stat)
