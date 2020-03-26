import pymystem3
from string import punctuation


m = pymystem3.Mystem()

stop_words = tuple(
    ["", "под", "там", "—", "о", "по", "в", "на", "и", "мы", "с", "для", "из", "под", "вы", "от", "а", "не", "как",
     "к", "что", "–", "это", "они", "наш", "до", "я", "быть", "этот",
     'бы', 'оно', 'ага'] +
    list(punctuation)
)


def check_word(word):
    word = word.strip()
    if word in stop_words:
        return

    return word


def tokenize(words):
    return [x for word in m.lemmatize(words)
            if (x := check_word(word))
            ]


__all__ = ("tokenize", )
