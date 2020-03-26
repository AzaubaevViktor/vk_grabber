import asyncio

from app import Application
from core import LoadConfig


async def main(count):
    app = Application(LoadConfig(), count)
    await app.warm_up()
    await app()


asyncio.run(main(100))
