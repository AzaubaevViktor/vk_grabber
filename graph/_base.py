from typing import Sequence, Type

from core import AttributeStorage


class _Base(AttributeStorage):
    _base_label_class = "_Base"

    @classmethod
    def _labels(cls) -> Sequence[Type["_Base"]]:
        models = []

        for klass in cls.__mro__:
            if klass.__name__ == cls._base_label_class:
                break

            models.append(klass)

        return models

    @classmethod
    def _label_processor(cls, klass) -> str:
        raise NotImplementedError()

    @classmethod
    def labels(cls):
        labels = []
        for klass in cls._labels():
            labels.append(cls._label_processor(klass))

        return ":".join(labels)
