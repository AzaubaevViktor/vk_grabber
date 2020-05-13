from core import Attribute, AttributeStorage


class Monitoring:
    pass


class PageAttribute(Attribute):
    pass


class BasePage(AttributeStorage):
    TEMPLATE = None


class DictPage(BasePage):
    TEMPLATE = 'dict'


class ListPage(BasePage):
    TEMPLATE = 'list'
