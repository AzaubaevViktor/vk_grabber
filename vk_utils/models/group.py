from core import AttributeStorage, Attribute


class VKGroup(AttributeStorage):
    id = Attribute()
    name = Attribute()
    screen_name = Attribute()
    is_closed = Attribute()
    type = Attribute()
    is_admin = Attribute()
    is_member = Attribute()
    is_advertiser = Attribute()
    photo_50 = Attribute()
    photo_100 = Attribute()
    photo_200 = Attribute()
