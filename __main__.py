import asyncio

from app import Application
from core import LoadConfig


async def main(*counts):
    app = Application(LoadConfig(), *counts)
    await app.warm_up()
    await app()


if __name__ == "__main__":
    asyncio.run(main(None, None, None))
