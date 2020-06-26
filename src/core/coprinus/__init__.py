"""
Модуль, собирающий ошибки
"""
from time import time
from traceback import format_exc

from core.monitor import ListPage, DictPage, PageAttribute


class CorpinusManager:
    class _CorpinusPage(ListPage):
        MAX_SIZE = 30

    class ExceptionPage(DictPage):
        moment = PageAttribute()
        # error_class = PageAttribute()
        text = PageAttribute()
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
        moment = time()
        self.page.append(
            self.ExceptionPage(
                id=f"error_{moment}",
                name=f"Error {moment}",
                moment=moment,
                text=format_exc(),
                args=args,
                kwargs=kwargs
            )
        )
