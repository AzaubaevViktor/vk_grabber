from core import AttributeStorage, Attribute


class ModelAttribute(Attribute):
    pass


class Model(AttributeStorage):
    _id = ModelAttribute(uid=True)

