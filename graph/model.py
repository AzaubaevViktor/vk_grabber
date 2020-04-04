from typing import Type

from ._base import _Base


class Model(_Base):
    _base_label_class = "Model"

    @classmethod
    def _label_processor(cls, klass: Type["Model"]) -> str:
        return klass.__name__
