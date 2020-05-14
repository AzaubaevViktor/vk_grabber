import json
from json import JSONEncoder
from typing import Optional, Tuple, Type, Any, Dict, Iterable, TypeVar, Callable

from core.log import Log
from core.searchable import SearchableSubclasses


class Attribute:
    class _DefaultNone:
        pass

    def __init__(self, description: Optional[str] = None,
                 default: Any = _DefaultNone(),
                 uid: bool = False,
                 method: Optional[Callable] = None):
        self.uid = uid
        self.name = None
        self.description = description
        self._default = default
        self.method = method

    @property
    def default(self):
        return self._default() if callable(self._default) else self._default

    @property
    def is_uid_attribute(self):
        return False

    def __get__(self, instance: "AttributeStorage", owner: Type["AttributeStorage"]):
        if instance is None:
            return self

        if self.method is not None:
            return self.method(instance)

        value = instance._storage.get(self.name, self.default)
        assert not isinstance(value, self._DefaultNone)
        return value

    def __set__(self, instance: "AttributeStorage", value: "Any"):
        if self.method is not None and not isinstance(value, self._DefaultNone) and value is not None:
            raise ValueError(f"You cannot set value {value} to property")

        instance._storage[self.name] = value

    @property
    def is_required(self):
        if self.method is not None:
            return False
        return isinstance(self.default, Attribute._DefaultNone)

    def copy(self) -> "Attribute":
        attr = Attribute(description=self.description,
                         default=self.default,
                         uid=self.uid)
        attr.name = self.name
        return attr

    @classmethod
    def property(cls, method):
        return cls(method=method)


class KwargsAttribute(Attribute):
    pass


class MetaAttributeStorage(type):
    logger = Log("MetaAttributeStorage")

    def __new__(mcs, name: str, bases: Tuple[Type["AttributeStorage"]], attrs: Dict[str, Any]):
        __attributes__ = attrs.get("__attributes__", None)
        __uids__ = attrs.get("__uids__", None)

        if __attributes__:
            raise NotImplementedError("Do not set __attributes__ manually")

        if __uids__:
            raise NotImplementedError("Do not set __uids__ manually")

        __kwargs_attribute__ = attrs.get("__kwargs_attributes__", None)
        if __kwargs_attribute__:
            raise NotImplementedError("Do not set __kwargs_attributes__ manually")

        __attributes__ = {}
        __uids__ = {}
        __kwargs_attribute__ = None
        __kwargs_attribute_class__ = None

        for base in bases:
            base: Type["AttributeStorage"]
            if hasattr(base, "__attributes__"):
                __attributes__.update(base.__attributes__)
            if hasattr(base, "__kwargs_attribute__"):
                if __kwargs_attribute__:
                    assert __kwargs_attribute__ is base.__kwargs_attribute__
                else:
                    __kwargs_attribute__ = base.__kwargs_attribute__
                    __kwargs_attribute_class__ = base.__name__
            if hasattr(base, "__uids__"):
                if base.__uids__:
                    __uids__.update(base.__uids__)

        for attr_name, attr_value in attrs.items():
            if not isinstance(attr_value, Attribute):
                continue

            attr_value.name = attr_name

            if attr_value.uid and not attr_value.is_uid_attribute:
                if isinstance(attr_value, KwargsAttribute):
                    raise AttributeError(f"{KwargsAttribute.__name__} cannot be uid")

                __uids__[attr_name] = attr_value

            if isinstance(attr_value, KwargsAttribute):
                if __kwargs_attribute__:
                    raise NameError("Two KwargsAttribute: "
                                    f"{__kwargs_attribute__.name} from {__kwargs_attribute_class__} "
                                    f"and {attr_name} from {name}")
                else:
                    __kwargs_attribute_class__ = name
                    __kwargs_attribute__ = attr_value
            elif isinstance(attr_value, Attribute):
                __attributes__[attr_name] = attr_value

        attrs['__attributes__'] = __attributes__
        attrs['__kwargs_attribute__'] = __kwargs_attribute__
        attrs['__uids__'] = __uids__

        return super().__new__(mcs, name, bases, attrs)


class AttributeStorageEncoder(JSONEncoder):
    def default(self, o):
        print(o)
        if isinstance(o, AttributeStorage):
            return {
                "@class": o.__class__.__name__,
                **dict(o)
            }
        return super().default(o)


def _attribute_storage_hook(dct):
    if "@class" in dct:
        msg_class_name = dct['@class']
        AttributeStorageClass = AttributeStorage.search(msg_class_name)
        del dct['@class']
        return AttributeStorageClass(**dct)
    return dct


AS_T = TypeVar("AS_T", "AttributeStorage", "AttributeStorage")


class AttributeStorage(SearchableSubclasses, metaclass=MetaAttributeStorage):
    __attributes__: Dict[str, Attribute]
    __kwargs_attribute__: Optional[Attribute] = None
    __uids__: Dict[str, Attribute]

    def __init__(self, **kwargs):
        self._storage = {}

        for k, attr in self.__attributes__.items():
            if not isinstance(attr, KwargsAttribute) \
                    and (k not in kwargs):
                if attr.is_required:
                    raise TypeError(f"Missed argument: {k}; Set value or set default")
                else:
                    setattr(self, k, attr.default)

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

    def __iter__(self) -> Iterable[Tuple[str, Any]]:
        kwarg_attr_name = None
        if self.__class__.__kwargs_attribute__:
            kwarg_attr_name = self.__class__.__kwargs_attribute__.name

        for name in self.__class__.__attributes__:
            if kwarg_attr_name and name == kwarg_attr_name:
                continue

            yield name, getattr(self, name, None)

        if kwarg_attr_name:
            # noinspection PyTypeChecker
            kwargs: dict = self.__kwargs_attribute__
            yield from kwargs.items()

    def serialize(self) -> str:
        return json.dumps(self, cls=AttributeStorageEncoder)

    @classmethod
    def deserialize(cls: Type[AS_T], data: str, force=False) -> AS_T:
        obj = json.loads(data, object_hook=_attribute_storage_hook)
        if (type(obj) is not cls) and not force:
            raise TypeError(f"Deserialized object must be {cls.__name__} type "
                            f"instead {type(obj).__name__}")
        return obj

    def __hash__(self):
        raise NotImplementedError()

    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False

        return self._storage == other._storage

    def __str__(self) -> str:
        attrs = "; ".join(
            f"{k}={getattr(self, k, None)}" for k in self.__attributes__
        )

        return f"<{self.__class__.__name__}: {attrs}>"

    def __repr__(self):
        attrs = "; ".join(
            f"{k}={getattr(self, k, None)}" for k in self.__uids__
        )

        return f"<{self.__class__.__name__}: {attrs}>"

