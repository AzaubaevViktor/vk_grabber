from typing import Optional

from core import Attribute, AttributeStorage


class PageAttribute(Attribute):
    def __init__(self, description: Optional[str] = None, default=None, uid: bool = False, method = None):
        super().__init__(description=description, default=default, uid=uid, method=method)


class BasePage(AttributeStorage):
    TEMPLATE = None

    id = PageAttribute()
    name = PageAttribute()

    def __init__(self, id: str, name: str, **kwargs):
        super().__init__(id=id, name=name, **kwargs)

    def to_dict(self) -> dict:
        return {
            **self._storage,
            'template': self.TEMPLATE
        }

    def page_info(self) -> dict:
        return {
            'id': self.id,
            'name': self.name
        }


class DictPage(BasePage):
    TEMPLATE = 'dict'


class ListPage(BasePage):
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

    def to_dict(self) -> dict:
        info = super(ListPage, self).to_dict()
        old_data = info.pop('data')
        new_data = []
        info['data'] = new_data

        for item in old_data:
            if isinstance(item, BasePage):
                new_data.append(item.to_dict())
            else:
                new_data.append(item)

        return info
