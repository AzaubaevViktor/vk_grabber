import pymystem3
from string import punctuation, whitespace


m = pymystem3.Mystem()

stop_words = tuple(
    ["", "под", "там", "—", "о", "по", "в", "на", "и", "мы", "с", "для", "из", "под", "вы", "от", "а", "не", "как",
     "к", "что", "–", "это", "они", "наш", "до", "я", "быть", "этот",
     'бы', 'оно', 'ага', "но", "то", "..."] +
    list(punctuation) +
    list(whitespace)
)

analyze_exclude = ['нгу']


def check_word(analyze_result):
    orig_word = analyze_result['text'].strip()

    try:
        word: str = analyze_result['analysis'][0]['lex'].strip()
    except (KeyError, IndexError):
        word: str = orig_word

    if word in stop_words:
        return

    if len(word) <= 2:
        return

    if word.isdigit():
        return

    if orig_word.lower() in analyze_exclude:
        return orig_word.lower()

    return word


def tokenize(words):
    return [x for word in m.analyze(words)
            if (x := check_word(word))
            ]


__all__ = ("tokenize", )
