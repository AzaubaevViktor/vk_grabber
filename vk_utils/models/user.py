from database import ModelAttribute, Model


class VKPerson(Model):
    id = ModelAttribute(uid=True)

    first_name = ModelAttribute(default=None)
    last_name = ModelAttribute(default=None)
    verified = ModelAttribute(default=None)
    sex = ModelAttribute(default=None)
    bdate = ModelAttribute(default=None)
    city = ModelAttribute(default=None)
    country = ModelAttribute(default=None)
    home_town = ModelAttribute(default=None)
    photo_400_orig = ModelAttribute(default=None)
    online = ModelAttribute(default=None)
    has_mobile = ModelAttribute(default=None)

    # Privacy
    deactivated = ModelAttribute(default=None)
    hidden = ModelAttribute(default=False)

    # contacts
    mobile_phone: str = ModelAttribute(default=None)
    home_phone: str = ModelAttribute(default=None)

    # education
    university: int = ModelAttribute(default=None)
    university_name: str = ModelAttribute(default=None)
    faculty: int = ModelAttribute(default=None)
    faculty_name: str = ModelAttribute(default=None)
    graduation: int = ModelAttribute(default=None)

    education_form = ModelAttribute(default=None)
    education_status = ModelAttribute(default=None)

    universities = ModelAttribute(default=None)
    schools = ModelAttribute(default=None)
    last_seen = ModelAttribute(default=None)
    occupation = ModelAttribute(default=None)

    is_closed = ModelAttribute(default=None)
    can_access_closed = ModelAttribute(default=None)

    online_app = ModelAttribute(default=None)
    online_mobile = ModelAttribute(default=None)
