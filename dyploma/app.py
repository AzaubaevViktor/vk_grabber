import asyncio

from app.base import BaseApplication
from core import LoadConfig, BaseWork
from dyploma.services.vk_ import LoadGroups, LoadParticipants, LoadPersonsPosts, LoadGroupPosts, LoadPostComments
from dyploma.services.word_ import WordKnifePost, WordKnifeComment


class DyplomaApplication(BaseApplication):
    def __init__(self, config: LoadConfig, force_clean=False):
        super().__init__(config)
        self.clean = config.app.clean
        self._force_clean = force_clean

    async def warm_up(self):
        if self.clean:
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

            self.log.important("⚠️ ⚠️ ⚠️ HERE WE DROP DATABASE")
            await self.ctx.db.delete_all(i_understand_delete_all=True)
            self.log.important("⚠️ ⚠️ ⚠️ HERE WE END DROP DATABASE...")

        await super(DyplomaApplication, self).warm_up()

        await self._add_handlers()

    async def __call__(self):
        first = await self.prepare_services(LoadGroups)

        second = await self.prepare_services(
            LoadParticipants,
            LoadPersonsPosts,
            LoadGroupPosts,
            LoadPostComments,
            WordKnifePost,
            WordKnifeComment,
        )

        await first
        await second

    async def prepare_services(self, *services):
        first_step_tasks = []
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