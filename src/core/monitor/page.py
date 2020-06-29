"""
Реализация страницы для мониторинга
"""
from typing import Optional

from core import Attribute, AttributeStorage


class PageAttribute(Attribute):
    """Отображаемое поле страницы"""
    def __init__(self, description: Optional[str] = None, default=None, uid: bool = False, method = None):
        super().__init__(description=description, default=default, uid=uid, method=method)


class BasePage(AttributeStorage):
    """Страница"""
    TEMPLATE = None

    id = PageAttribute()
    name = PageAttribute()

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id=id, name=name, **kwargs)

    def __iter__(self):
        for key, value in super(BasePage, self).__iter__():
            if isinstance(value, BasePage):
                value = value.to_dict()
            yield key, value

    def to_dict(self) -> dict:
        return {
            **dict(self),
            'template': self.TEMPLATE
        }

    def page_info(self) -> dict:
        return {
            'id': self.id,
            'name': self.name
        }


class DictPage(BasePage):
    """Страница-словарь"""
    TEMPLATE = 'dict'


class ListPage(BasePage):
    """Страница-список"""
    TEMPLATE = 'list'
    MAX_SIZE = None  # TODO: Tests

    data = PageAttribute()

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id, name, **kwargs)
        if self.data is None:
            self.data = []

    def append(self, sub_page: BasePage):
        self.data.append(sub_page)
        if self.MAX_SIZE and len(self.data) > self.MAX_SIZE:
            self.data.pop(0)

    def __contains__(self, id_: str):
        return self[id_] is not None

    def __getitem__(self, id_: str):
        for item in self.data:
            if hasattr(item, "id") and id_ == item.id:
                return item
        return None

    def to_dict(self) -> dict:
        info = super(ListPage, self).to_dict()
        old_data = info.pop('data')

        info['data'] = new_data = []

        if getattr(self, "sorted_function", None):
            iter_items = (item for item in sorted(old_data, key=self.sorted_function))
        else:
            iter_items = old_data

        for item in iter_items:
            if isinstance(item, BasePage):
                new_data.append(item.to_dict())
            else:
                new_data.append(item)

        return info
