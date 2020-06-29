import asyncio
from typing import Type

from app.base import BaseApplication, BaseWorkApp
from core import LoadConfig, BaseWork, CorpinusManager
# from dyploma.services.vk_ import LoadGroups, LoadParticipants, LoadPersonsPosts, LoadGroupPosts, LoadPostComments
from .services.vk_ng import LoadGroups, LoadGroupInfo, LoadPersonFromGroup, LoadPersonInfo, LoadPostFromGroup, LoadPostFromPerson
from dyploma.services.word_ import WordKnifePost, WordKnifeComment
from .services.word_stats import WordsUpdater


class DyplomaApplication(BaseApplication):
    def __init__(self, config: LoadConfig, force_clean=False):
        super().__init__(config)
        self.clean = config.app.clean
        self._force_clean = force_clean

    async def warm_up(self):
        await super(DyplomaApplication, self).warm_up()
        self.ctx.mon.main_page.info = "WarmUp"

        if self.clean:
            self.ctx.mon.main_page.info = "🏴‍☠️ Prepare to clean database"

            if not self._force_clean:
                self.log.important("⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️")
                self.log.important("⚠️⚠️⚠️                           ⚠️⚠️⚠️")
                self.log.important("⚠️⚠️⚠️ NOW I DELETE ALL DATABASE ⚠️⚠️⚠️")
                self.log.important(f"⚠️⚠️⚠️{self.ctx.db.db_name:^27}⚠️⚠️⚠️")
                self.log.important("⚠️⚠️⚠️                           ⚠️⚠️⚠️")
                self.log.important("⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️⚠️")
                self.log.important("This", name=self.ctx.db.db_name, db=self.ctx.db)

                countdown = 10
                for i in range(countdown):
                    await asyncio.sleep(1)
                    self.log.warning(countdown - i)

            self.ctx.mon.main_page.info = "💀 Cleaning Database"

            self.log.important("⚠️ ⚠️ ⚠️ HERE WE DROP DATABASE")
            await self.ctx.db.delete_all(i_understand_delete_all=True)
            self.log.important("⚠️ ⚠️ ⚠️ HERE WE END DROP DATABASE...")

            self.ctx.mon.main_page.info = "Database cleaned"

        await self._add_handlers()

    async def __call__(self):
        first = await self.prepare_services(LoadGroups)

        second = await self.prepare_services(
            LoadGroupInfo,
            LoadPersonFromGroup,
            LoadPersonInfo,
            LoadPostFromGroup,
            LoadPostFromPerson,
            WordKnifePost,
            WordKnifeComment,
            WordsUpdater
        )

        self.ctx.mon.main_page.info = "Run LoadGroups"
        await first

        self.ctx.mon.main_page.info = "Work"
        await second

    async def prepare_services(self, *services: Type[BaseWorkApp]):
        first_step_tasks = []

        self.ctx.mon.main_page.info = f"Prepare {len(services)} services"

        for item in services:
            if self.config.app.services[item.__name__]:
                self.log.info("Service postponed", service=item)

                first_step_tasks.append(item(self.ctx)())
            else:
                self.log.info("Service disabled by config", service=item)
        return asyncio.gather(*first_step_tasks)

    async def _add_handlers(self):
        import signal
        import functools

        loop = asyncio.get_running_loop()
        for signame in {'SIGINT', 'SIGTERM'}:
            loop.add_signal_handler(
                getattr(signal, signame),
                functools.partial(self._gracefull, signame, loop))

    def _gracefull(self, signame, loop):
        self.log.warning("⚠️ Exit handler", signame=signame, loop=loop)
        BaseWork.need_stop = True