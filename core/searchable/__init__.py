from typing import Type, TypeVar

_TM = TypeVar("_TM")


class SearchableSubclasses:
    @staticmethod
    def _all_subclasses(cls):
        for klass in cls.__subclasses__():
            klass: SearchableSubclasses
            yield klass
            yield from SearchableSubclasses._all_subclasses(klass)

    @classmethod
    def all_subclasses(cls):
        return cls._all_subclasses(cls)

    @staticmethod
    def _search(cls: _TM, name: str) -> Type[_TM]:
        for klass in SearchableSubclasses._all_subclasses(cls):
            klass: Type[_TM]
            if klass.__name__ == name:
                return klass

        raise NameError(f"Not found service with name {name}. "
                        f"Class must be subclass of `Service`",
                        name, tuple(klass.__name__ for klass in SearchableSubclasses._all_subclasses(cls)))

    @classmethod
    def search(cls: _TM, name: str) -> Type[_TM]:
        return cls._search(cls, name)
