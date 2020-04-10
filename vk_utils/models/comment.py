from core import Attribute
from database import ModelAttribute, Model


class VKComment(Model):
    id = ModelAttribute(uid=True)

    text = ModelAttribute()
    date = ModelAttribute()
    from_id = ModelAttribute()
    parents_stack = ModelAttribute()
    likes = ModelAttribute()
    attachments = ModelAttribute(default=None)

    thread = Attribute()  # Не записывается в mongo

    # Добавляются сами
    post_id = ModelAttribute(default=None)
    owner_id = ModelAttribute(default=None)

    def get_thread(self):
        for item in self.thread['items']:
            yield VKComment(**item)
