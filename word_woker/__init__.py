import pymystem3


m = pymystem3.Mystem()


def tokenize(words):
    return [x for word in m.lemmatize(words) if (x := word.strip())]


__all__ = ("tokenize", )
