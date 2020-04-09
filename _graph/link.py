from typing import Type

from ._base import _Base


class Link(_Base):
    LTR = None

    _base_label_class = "Link"

    @classmethod
    def _label_processor(cls, klass: Type["Link"]) -> str:
        result = ""
        for ch in klass.__name__:
            if ch.isupper():
                result += "_" + ch
            else:
                result += ch

        if result[0] == "_":
            result = result[1:]

        return result.upper()
