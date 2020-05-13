from typing import Optional

from core import Attribute, AttributeStorage


class PageAttribute(Attribute):
    def __init__(self, description: Optional[str] = None, default=None, uid: bool = False):
        super().__init__(description, default, uid)


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


class DictPage(BasePage):
    TEMPLATE = 'dict'


class ListPage(BasePage):
    TEMPLATE = 'list'
