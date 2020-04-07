from typing import Sequence, List

from graph import Model


class QPart:
    def __init__(self, q, kwargs):
        self.q = q
        self.kwargs = kwargs


class Q:
    driver = None

    def __init__(self):
        self.parts: List[QPart] = []

    def __iadd__(self, other: QPart):
        assert isinstance(other, QPart)
        self.parts.append(other)

    def run(self):
        raise NotImplementedError()

    @classmethod
    def connect(self, driver):
        self.driver = driver

    @classmethod
    def cleanup(self):
        raise NotImplementedError()

    @classmethod
    def create(cls, *nodes: Model):
        raise NotImplementedError()

    @classmethod
    def var(cls, name, q_part: QPart):
        raise NotImplementedError()

    @classmethod
    def ret(cls, what: str):
        raise NotImplementedError()

    @classmethod
    def update(cls, *nodes: Model):
        raise NotImplementedError()

    @classmethod
    def find(cls, model_query):
        raise NotImplementedError()
