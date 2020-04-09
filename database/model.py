from typing import Type

from core import Attribute, AttributeStorage


class ModelAttribute(Attribute):
    def __get__(self, instance: "Model", owner: Type["Model"]):
        if instance is None:
            return self

        value = instance._storage.get(self.name, self.default)
        if isinstance(value, self._DefaultNone):
            return None
        return value

    def __set__(self, instance: "Model", value: "Any"):
        super().__set__(instance, value)
        instance._updates[self.name] = value


class Model(AttributeStorage):
    _id = ModelAttribute(uid=True, default=None)

    def __init__(self, **kwargs):
        self._storage = {}
        self._updates = {}

        # for k, attr in self.__attributes__.items():
        #     if not isinstance(attr, KwargsAttribute) \
        #             and (k not in kwargs):
        #         setattr(self, k, attr.default)

        for k, v in {**kwargs}.items():
            if k in self.__attributes__:
                setattr(self, k, v)
                del kwargs[k]

        if self.__class__.__kwargs_attribute__:
            setattr(self, self.__class__.__kwargs_attribute__.name, kwargs)
        else:
            if kwargs:
                raise TypeError(f"In class {self.__class__.__name__}, "
                                f"extra arguments: {','.join(kwargs.keys())}. "
                                f"Try one of: {self.__attributes__.keys()}")

    def verificate(self):
        for k, attr in self.__attributes__.items():
            if isinstance(self._storage.get(k, Attribute._DefaultNone()), Attribute._DefaultNone):
                if isinstance(attr.default, Attribute._DefaultNone):
                    raise ValueError(f"Set {self.__class__.__name__}.{k}")
        return True

    def serialize(self) -> dict:
        result = {}
        for k, attr in self.__attributes__.items():
            value = getattr(self, k, None)
            if not isinstance(value, Attribute._DefaultNone) and value is not None:
                result[k] = value

        return result

    def query(self) -> dict:
        return self._storage

    def updates(self) -> dict:
        return self._updates

    def drop_updates(self):
        self._updates = {}