from enum import Enum
from time import time

from database import Model, ModelAttribute


class State(Enum):
    NEW = None
    IN_PROGRESS = "IN_PROGRESS"
    FINISHED = "FINISHED"

    ERROR = "ERROR"
    SKIP = "SKIP"

    DELETE = "DELETE"


class Word(Model):
    word: str = ModelAttribute()
    date: int = ModelAttribute()
    from_id: int = ModelAttribute()
    post_id: int = ModelAttribute()


class WordSummarize(Model):
    word: str = ModelAttribute()
    count: int = ModelAttribute()
    update_at: int = ModelAttribute(method=lambda: time())