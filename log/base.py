import datetime
import os
import random
from enum import Enum
from inspect import getframeinfo, stack

from colorama import Fore, Back, Style
from traceback import format_exc


class LogLevel(Enum):
    DEEP = -100
    DEBUG = 0
    INFO = 100
    IMPORTANT = 200
    WARNING = 300
    EXCEPTION = 400
    ERROR = 1000


class Log:
    TIME_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    LEVEL_COLOR = {
        LogLevel.DEEP: Fore.LIGHTBLACK_EX,
        LogLevel.DEBUG: Fore.WHITE,
        LogLevel.IMPORTANT: Back.BLUE + Fore.LIGHTYELLOW_EX,
        LogLevel.WARNING: Back.LIGHTMAGENTA_EX + Fore.LIGHTCYAN_EX,
        LogLevel.EXCEPTION: Back.LIGHTRED_EX,
        LogLevel.ERROR: Back.RED
    }
    pid_colors = {}
    colors_list = [
        Fore.RED,
        Fore.BLUE,
        Fore.GREEN,
        Fore.YELLOW,
        Fore.MAGENTA,
        Fore.CYAN
    ]

    def __init__(self, name: str):
        self.name = name
        self._level: LogLevel = LogLevel.DEBUG

    @property
    def level(self) -> LogLevel:
        return self._level

    @level.setter
    def level(self, level: LogLevel):
        if not isinstance(level, LogLevel):
            raise TypeError(f"{level} isn't correct type for Log level. "
                            f"Try to use {LogLevel.__name__} values")
        self._level = level

    def _frame(self, deep):
        caller = getframeinfo(stack()[deep][0])
        return os.path.relpath(caller.filename), caller.function, caller.lineno

    def _print(self, level: LogLevel, *args, **kwargs):
        if level.value >= self._level.value:
            now = datetime.datetime.now()
            _args = ' '.join(map(str, args)) if args else ''
            _kwargs = ' '.join((f"{k}={v}" for k, v in kwargs.items())) if kwargs else ''
            _level_name_colorize = f"{self.LEVEL_COLOR.get(level, '')}{level.name:^9}{Style.RESET_ALL}"
            file_name, fun_name, lineno = self._frame(3)

            _pid = os.getpid()
            if _pid not in self.pid_colors:
                self.pid_colors[_pid] = random.choice(self.colors_list)
            pid = f"{self.pid_colors[_pid]}{_pid}{Style.RESET_ALL}"

            print(f"[{now.strftime(self.TIME_FORMAT)}] [{_level_name_colorize}] /{pid}/ {self.name} {Fore.LIGHTBLACK_EX}{file_name}:{lineno} {fun_name}{Style.RESET_ALL}: {_args} {_kwargs}")

    def deep(self, *args, **kwargs):
        self._print(LogLevel.DEEP, *args, **kwargs)

    def debug(self, *args, **kwargs):
        self._print(LogLevel.DEBUG, *args, **kwargs)

    def info(self, *args, **kwargs):
        self._print(LogLevel.INFO, *args, **kwargs)

    def important(self, *args, **kwargs):
        self._print(LogLevel.IMPORTANT, *args, **kwargs)

    def warning(self, *args, **kwargs):
        self._print(LogLevel.WARNING, *args, **kwargs)

    def exception(self, *args, **kwargs):
        self._print(LogLevel.EXCEPTION, *args, **kwargs, _err=f'\n{format_exc()}')

    def error(self, *args, **kwargs):
        self._print(LogLevel.ERROR, *args, **kwargs)
