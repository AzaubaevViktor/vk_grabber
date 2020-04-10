import asyncio
import inspect

from core import Log


class Chaos:
    last_index = 0

    def __init__(self, start=None, name='', repeats=0):
        self.last_index += 1
        self.log = Log(f'Chaos:{name or self.last_index}')
        self.start = [None] if start is None else start
        self.chain = []
        self.repeats = repeats

    def __rshift__(self, other):
        __call__ = other

        if not (inspect.iscoroutine(__call__) or inspect.isfunction(__call__)):
            if not hasattr(other, "__call__"):
                raise TypeError("Must be function or instance with __call__")
            __call__ = other.__call__

        if not inspect.isasyncgenfunction(__call__):
            raise TypeError("Must be async generator")

        self.chain.append(__call__)

        return self

    async def run(self):
        # create queues
        self.log.info("Create links")
        tasks = []
        input_q = asyncio.Queue()

        for item in self.start:
            await input_q.put(item)

        for method in self.chain:
            output_q = asyncio.Queue()

            tasks.append(self._create_link(input_q, method, output_q))

            input_q = output_q

        self.log.info("Run chain")

        await asyncio.gather(*tasks)

    async def _create_link(self, input_q: asyncio.Queue, method, output_q: asyncio.Queue) :
        sig = inspect.signature(method)

        assert len(sig.parameters)

        param: inspect.Parameter = tuple(sig.parameters.values())[0]

        repeat_count = 0

        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            raise NotImplementedError()
        else:
            while True:
                try:
                    item = await asyncio.wait_for(input_q.get(), (repeat_count + 1))

                    repeat_count = 0
                    self.log.info("Processing", item=item)

                    async for result in method(item):
                        self.log.info("Result", item=item, result=result)
                        await output_q.put(result)

                except asyncio.TimeoutError:
                    repeat_count += 1

                    if repeat_count >= self.repeats:
                        break
