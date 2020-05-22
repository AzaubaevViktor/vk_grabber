from time import time

from database import Model, ModelAttribute


class Word(Model):
    word: str = ModelAttribute()
    date: int = ModelAttribute()
    from_id: int = ModelAttribute()
    post_id: int = ModelAttribute()


class WordSummarize(Model):
    word: str = ModelAttribute()
    count: int = ModelAttribute()
    update_at: int = ModelAttribute(method=lambda: time())