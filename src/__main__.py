import asyncio
from sys import argv

from dyploma import DyplomaApplication
from core import LoadConfig


async def main():
    if len(argv) != 2:
        app_name = argv[0] if argv else "app"
        print(f"Please use {app_name} <path/to/config_file.yaml>")
        print("Instead:")
        print(argv)
    app = DyplomaApplication(LoadConfig(argv[1]))
    await app.warm_up()
    await app()


if __name__ == "__main__":
    asyncio.run(main())
