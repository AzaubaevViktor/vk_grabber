from core import AttributeStorage, Attribute


class VKUser(AttributeStorage):
    id = Attribute(uid=True)

    first_name = Attribute(default=None)
    last_name = Attribute(default=None)
    deactivated = Attribute(default=None)
    verified = Attribute(default=None)
    sex = Attribute(default=None)
    bdate = Attribute(default=None)
    city = Attribute(default=None)
    country = Attribute(default=None)
    home_town = Attribute(default=None)
    photo_400_orig = Attribute(default=None)
    online = Attribute(default=None)
    has_mobile = Attribute(default=None)

    # contacts
    mobile_phone: str = Attribute(default=None)
    home_phone: str = Attribute(default=None)

    # education
    university: int = Attribute(default=None)
    university_name: str = Attribute(default=None)
    faculty: int = Attribute(default=None)
    faculty_name: str = Attribute(default=None)
    graduation: int = Attribute(default=None)

    universities = Attribute(default=None)
    schools = Attribute(default=None)
    last_seen = Attribute(default=None)
    occupation = Attribute(default=None)

    is_closed = Attribute(default=None)
    can_access_closed = Attribute(default=None)
