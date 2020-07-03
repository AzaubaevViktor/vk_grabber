"""
Реализация страницы для мониторинга
"""
from typing import Optional, Tuple, Type, Dict, Any

from core import Attribute, AttributeStorage
from core.attribute_storage.attribute_storage import MetaAttributeStorage


class PageAttribute(Attribute):
    """Отображаемое поле страницы"""
    def __init__(self, description: Optional[str] = None, default=None, uid: bool = False, method = None):
        super().__init__(description=description, default=default, uid=uid, method=method)


class PageMeta(MetaAttributeStorage):
    """Метакласс для отображения только PageAttribute"""
    def __new__(mcs, name: str, bases: Tuple[Type["AttributeStorage"]], attrs: Dict[str, Any]):
        klass = super().__new__(mcs, name, bases, attrs)

        __attributes__: Dict[str, Attribute] = klass.__attributes__
        klass.__attributes__ = {
            k: attr for k, attr in __attributes__.items()
            if isinstance(attr, PageAttribute)
        }

        return klass


class BasePage(AttributeStorage, metaclass=PageMeta):
    """Страница"""
    TEMPLATE = None

    id = PageAttribute(default=None)  # add default random_id
    name = PageAttribute(default=None)  # name the same

    def __init__(self, id: str = None, name: str = None, **kwargs):
        kwargs['id'] = id
        kwargs['name'] = name
        super().__init__(**kwargs)

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

    def __init__(self, id: str = None, name: str = None, **kwargs):
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
