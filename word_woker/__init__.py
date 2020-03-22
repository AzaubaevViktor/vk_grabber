import pymystem3
from string import punctuation


m = pymystem3.Mystem()

stop_words = tuple(
    ["", "под", "там", "—", "о", "по", "в", "на", "и", "мы", "с", "для"] +
    list(punctuation)
)


def tokenize(words):
    return [x for word in m.lemmatize(words)
            if ((x := word.strip()) not in stop_words)
            ]


__all__ = ("tokenize", )
