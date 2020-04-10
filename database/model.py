from typing import Type, Optional, Dict, Any

from core import Attribute, AttributeStorage


class ModelAttribute(Attribute):
    def __init__(self, description: Optional[str] = None,
                 default: Any = Attribute._DefaultNone(),
                 uid: bool = False):
        self._name = None
        super().__init__(description, default, uid)

    @property
    def name(self):
        if not self.uid:
            return self._name
        return "_id"

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def is_id_alias(self):
        return self.uid and self._name != "_id"

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
    __attributes__: Dict[str, ModelAttribute]
    __kwargs_attribute__: Optional[ModelAttribute] = None
    __uids__: Dict[str, ModelAttribute]

    _id = ModelAttribute(uid=True, default=None)

    def __init__(self, **kwargs):
        self._storage = {}
        self._updates = {}

        for k, attr in self.__attributes__.items():
            if not isinstance(attr, Attribute):
                raise TypeError(f"Use {Attribute.__name__} instance instead {attr}")

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
            if not isinstance(self._storage.get(k, Attribute._DefaultNone()), Attribute._DefaultNone):
                continue

            if not isinstance(attr.default, Attribute._DefaultNone):
                continue

            if attr.is_id_alias:
                continue

            raise ValueError(f"Set {self.__class__.__name__}.{k}")
        return True

    def serialize(self) -> dict:
        result = {}
        for k, attr in self.__attributes__.items():
            if not isinstance(attr, ModelAttribute):
                continue

            if attr.is_id_alias:
                continue

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

    @classmethod
    def soft_create(cls, **kwargs):
        for k in tuple(kwargs.keys()):
            if k not in cls.__attributes__:
                del kwargs[k]

        return cls(**kwargs)
