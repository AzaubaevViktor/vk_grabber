"""
Модуль, собирающий ошибки
"""
from time import time
from traceback import format_exc

from core.monitor import ListPage, DictPage, PageAttribute


class CorpinusManager:
    """Управление сбором ошибок"""

    class _CorpinusPage(ListPage):
        """Страница с отображением ошибок"""
        MAX_PER_PAGE = 30

    class ExceptionPage(DictPage):
        """Страница с описанием ошибки"""
        moment = PageAttribute()
        # error_class = PageAttribute()
        trace = PageAttribute()
        args = PageAttribute()
        kwargs = PageAttribute()

    def __init__(self):
        self.page = self._CorpinusPage(
            id="corpinus",
            name="Errors"
        )

        from core import log
        log.Log.corpinus = self.catch

    def catch(self, *args, **kwargs):
        """Захват ошибки"""
        moment = time()
        self.page.append(
            self.ExceptionPage(
                id=f"error_{moment}",
                name=f"Error {moment}",
                moment=moment,
                trace=format_exc(),
                args=tuple(str(arg) for arg in args) if args else None,
                kwargs={k: str(v) for k, v in kwargs.items()} if kwargs else None
            )
        )
