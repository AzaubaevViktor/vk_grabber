from database import ModelAttribute, Model


class VKComment(Model):
    id = ModelAttribute(uid=True)

    text = ModelAttribute()
    date = ModelAttribute()
    from_id = ModelAttribute()
