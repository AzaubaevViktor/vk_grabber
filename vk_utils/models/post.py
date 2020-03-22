from core import AttributeStorage, Attribute


class VKPost(AttributeStorage):
    id = Attribute()
    from_id = Attribute()
    owner_id = Attribute()
    date = Attribute()
    marked_as_ads = Attribute()
    post_type = Attribute()
    text = Attribute()
    attachments = Attribute(default=None)
    post_source = Attribute()
    comments = Attribute()
    likes = Attribute()
    reposts = Attribute()
    views = Attribute(default=None)

    is_pinned = Attribute(default=None)
    is_favorite = Attribute()
    edited = Attribute(default=False)
    copy_history = Attribute(default=None)
