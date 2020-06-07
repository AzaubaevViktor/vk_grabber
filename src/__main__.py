import asyncio
from sys import argv

from dyploma import DyplomaApplication
from core import LoadConfig


async def main():
    app = DyplomaApplication(LoadConfig(argv[1]))
    await app.warm_up()
    await app()


if __name__ == "__main__":
    asyncio.run(main())
