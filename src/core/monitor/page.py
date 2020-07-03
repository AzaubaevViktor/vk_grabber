"""
Реализация страницы для мониторинга
"""
from typing import Optional, Tuple, Type, Dict, Any, Callable

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
    MAX_PER_PAGE = None
    MAX_ITEMS = None

    data = PageAttribute()

    sorted_function: Callable[[Any], float]
    SORT_DIRECTION_LARGER_TOP = True

    def __init__(self, id: str = None, name: str = None, **kwargs):
        super().__init__(id, name, **kwargs)
        if self.data is None:
            self.data = []

    def append(self, sub_page: BasePage):
        assert sub_page.id not in self.data, "Use update"

        self.data.append(sub_page)

        if self.MAX_ITEMS and len(self.data) > self.MAX_ITEMS:
            self._do_sort_data()
            self.data.pop(-1)

    def update(self, sub_page: BasePage):
        if sub_page.id in self:
            item_to_remove = self[sub_page.id]
            self.data.remove(item_to_remove)

        self.append(sub_page)

    def __contains__(self, id_: str):
        return self[id_] is not None

    def __getitem__(self, id_: str):
        for item in self.data:
            if hasattr(item, "id") and id_ == item.id:
                return item
        return None

    def _reverse_sorted_f(self, item):
        return - self.sorted_function(item)

    def _do_sort_data(self):
        if getattr(self, "sorted_function", None):
            sorted_f = self.sorted_function
            if self.SORT_DIRECTION_LARGER_TOP:
                sorted_f = self._reverse_sorted_f

            self.data.sort(
                key=sorted_f
            )

    def to_dict(self) -> dict:
        self._do_sort_data()

        info = super(ListPage, self).to_dict()
        info['count'] = len(self.data)
        old_data = info.pop('data')[:self.MAX_PER_PAGE]

        info['data'] = new_data = []

        for item in old_data:
            if isinstance(item, BasePage):
                new_data.append(item.to_dict())
            else:
                new_data.append(item)

        return info
