from typing import Type

from ._base import _Base


class Model(_Base):
    _base_label_class = "Model"

    @classmethod
    def _label_processor(cls, klass: Type["Model"]) -> str:
        return klass.__name__

    @classmethod
    def dummy(cls, **params):
        return cls.Dummy()(**params)

    @classmethod
    def Dummy(cls):
        attrs = {}
        for name, attr in cls.__attributes__.items():
            new_attr = attr.copy()
            new_attr.default = None
            attrs[name] = new_attr
        Dummy = type("Dummy", (cls,), attrs)
        return Dummy
