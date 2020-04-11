import asyncio
from sys import argv

from app import Application
from core import LoadConfig


async def main():
    app = Application(LoadConfig(argv[1]))
    await app.warm_up()
    await app()


if __name__ == "__main__":
    asyncio.run(main())
