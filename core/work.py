import asyncio

from core import Log


class BaseWork:
    INPUT_REPEATS = 0

    def __init__(self):
        self.log = Log(self.__class__.__name__)
        self._state = None
        self.state = "Base class initialized"

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self.log.info(self._state)

    async def warm_up(self):
        pass

    async def input(self):
        raise NotImplementedError()

    async def process(self, item):
        raise NotImplementedError()

    async def update(self, result):
        raise NotImplementedError()

    async def shutdown(self):
        pass

    async def __call__(self):
        self.state = "Warming up"
        await self.warm_up()

        repeats_count = 0

        while True:
            self.state = "Wait for new item"
            async for item in self.input():
                repeats_count = 0
                self.state = f"{item} => ???"
                async for result in self.process(item):
                    self.state = f"{item} => {result}"
                    await self.update(result)
                    self.state = f"{item} => ???"

                self.state = "Wait for new item"

            if repeats_count < self.INPUT_REPEATS:
                repeats_count += 1
                self.state = f"Wait items, repeat №{repeats_count}"
                await asyncio.sleep(repeats_count)
            else:
                break

        self.state = "Shutdown"
        await self.shutdown()
        self.state = "Finished"