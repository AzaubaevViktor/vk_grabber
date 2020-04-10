import asyncio

from app import Application
from core import LoadConfig


async def main(*counts, **kwargs):
    app = Application(LoadConfig(), *counts, **kwargs)
    await app.warm_up()
    await app()


if __name__ == "__main__":
    asyncio.run(main(10, 10, 10, clean=False))
