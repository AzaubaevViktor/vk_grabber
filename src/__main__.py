import asyncio
import os
from sys import argv

from dyploma import DyplomaApplication
from core import LoadConfig, Config
from vk_utils.get_token import UpdateToken


async def default_cmd(config: Config):
    app = DyplomaApplication(config)
    await app.warm_up()
    return await app()


async def auth(config: Config):
    update_token = UpdateToken(config.vk)

    return await update_token()


commands = {
    'auth': auth
}


async def main():
    if len(argv) < 2:
        app_name = argv[0] if argv else "app"
        print(f"Please use {app_name} <path/to/config_file.yaml> [command]")
        print("Instead:")
        print(argv)
    print(f"CWD: {os.getcwd()}")

    config = LoadConfig(argv[1])

    command_name = argv[2] if len(argv) >= 3 else None
    print(f"Execute command: {command_name}")

    command = commands.get(command_name, default_cmd)

    answer = await command(config)
    if answer:
        print(f"Application finished with answer {answer}")


if __name__ == "__main__":
    asyncio.run(main())
