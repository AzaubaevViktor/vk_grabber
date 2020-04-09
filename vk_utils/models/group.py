from database import Model, ModelAttribute


class VKGroup(Model):
    id = ModelAttribute(uid=True)
    name = ModelAttribute()
    screen_name = ModelAttribute()
    description = ModelAttribute()

    is_closed = ModelAttribute()
    type = ModelAttribute()
    is_admin = ModelAttribute()
    is_member = ModelAttribute()
    is_advertiser = ModelAttribute()
    photo_200 = ModelAttribute()
