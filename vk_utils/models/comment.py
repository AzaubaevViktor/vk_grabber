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
    reply_to_user = ModelAttribute(default=None)
    reply_to_comment = ModelAttribute(default=None)

    thread = Attribute(default=None)  # Не записывается в mongo

    # Добавляются сами
    post_id = ModelAttribute(default=None)
    owner_id = ModelAttribute(default=None)

    def get_thread(self):
        if self.thread is None:
            return

        for item in self.thread['items']:
            yield VKComment(**item)
