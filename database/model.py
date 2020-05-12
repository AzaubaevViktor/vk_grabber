from typing import Type, Optional, Dict, Any

from core import Attribute, AttributeStorage, Log


class ModelAttribute(Attribute):
    def __init__(self, description: Optional[str] = None,
                 default: Any = Attribute._DefaultNone(),
                 uid: bool = False):
        self._name = None
        super().__init__(description, default, uid)

    @property
    def name(self):
        return self._name

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


class _UidAttribute(ModelAttribute):
    logger = Log("_UidAttribute")

    def __init__(self):
        super().__init__(description="UID calculated attribute for MongoDB",
                         default=None,
                         uid=True)

    @property
    def is_uid_attribute(self):
        return True

    @property
    def is_id_alias(self):
        return False

    @property
    def name(self):
        return "_id"

    @name.setter
    def name(self, value):
        if value is not None:
            if value != '_id':
                raise ValueError("Use `ModelAttribute(uid=True)`")

    def _hash_method(self, w):
        import hashlib
        h = hashlib.md5(w)
        return h.digest().decode("base64")

    def __get__(self, instance: "Model", owner: Type["Model"]):
        if instance is None:
            return self

        aliases = []

        for attr_name, attr in instance.__attributes__.items():
            if isinstance(attr, _UidAttribute):
                continue

            if not attr.is_id_alias:
                continue

            aliases.append(attr_name)

        aliases.sort()

        if len(aliases) == 0:
            raise ValueError("You need to set one or more ModelAttribute(uid=True)")

        if super(_UidAttribute, self).__get__(instance, owner) is not None:
            raise ValueError("Not alowed to directly change _id field")

        s = "/".join(str(value := getattr(instance, key)) + ":" + type(value).__name__ for key in aliases)

        self.logger.debug(uid=s)

        return s


class Model(AttributeStorage):
    COLLECTION: str = None

    __attributes__: Dict[str, ModelAttribute]
    __kwargs_attribute__: Optional[ModelAttribute] = None
    __uids__: Dict[str, ModelAttribute]

    _id = _UidAttribute()

    # noinspection PyMissingConstructor
    def __init__(self, **kwargs):
        self._storage = {}
        self._updates = {}

        for k, attr in self.__attributes__.items():
            if not isinstance(attr, Attribute):
                raise TypeError(f"Use {Attribute.__name__} instance instead {attr}")

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

            if isinstance(attr, ModelAttribute) and attr.is_id_alias:
                continue

            raise ValueError(f"Set {self.__class__.__name__}.{k}")
        return True

    def serialize(self) -> dict:
        result = {}
        for k, attr in self.__attributes__.items():
            if not isinstance(attr, ModelAttribute):
                continue

            value = getattr(self, k, None)
            if not isinstance(value, Attribute._DefaultNone) and value is not None:
                result[k] = value

        return result

    @classmethod
    def query(cls, query: Dict) -> Dict:
        result_query = {}

        for key, v in query.items():
            attr = getattr(cls, key, None)

            assert isinstance(attr, ModelAttribute)

            if attr is not None:
                result_query[key] = v
            else:
                result_query[attr.name] = v

        return result_query

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

    def __repr__(self):
        attrs = "; ".join(
            f"{k}={getattr(self, k, None)}" for k, attr in self.__uids__.items() if not attr.is_id_alias
        )

        return f"<{self.__class__.__name__}: {attrs}>"
