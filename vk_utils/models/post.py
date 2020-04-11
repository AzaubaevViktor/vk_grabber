from database import Model, ModelAttribute


class VKPost(Model):
    id = ModelAttribute()
    from_id = ModelAttribute()
    owner_id = ModelAttribute()
    date = ModelAttribute()
    marked_as_ads = ModelAttribute(default=None)
    post_type = ModelAttribute()
    text = ModelAttribute()
    attachments = ModelAttribute(default=None)
    post_source = ModelAttribute()
    comments = ModelAttribute()
    likes = ModelAttribute()
    reposts = ModelAttribute()
    views = ModelAttribute(default=None)

    is_pinned = ModelAttribute(default=None)
    is_favorite = ModelAttribute()
    edited = ModelAttribute(default=False)
    copy_history = ModelAttribute(default=None)
    signer_id = ModelAttribute(default=None)
    reply_owner_id = ModelAttribute(default=None)
    reply_post_id = ModelAttribute(default=None)
    final_post = ModelAttribute(default=False)
    copyright = ModelAttribute(default=None)

    geo = ModelAttribute(default=None)
    friends_only: bool = ModelAttribute(default=False)

    # TODO: Move into different class
    is_checked: bool = ModelAttribute(default=False)
