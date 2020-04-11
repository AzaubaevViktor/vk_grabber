import pymystem3
from string import punctuation, whitespace


m = pymystem3.Mystem()

replaces = {
    '\n': ' '
}

good_chars = "абвгдежзийклмнопрстуфхцчшщъыьэюя"
good_chars += good_chars.upper()
good_chars += " -"
good_chars += "".join(replaces.keys())


stop_words = tuple(
    ["", "под", "там", "о", "по", "в", "на", "и", "мы", "с", "для", "из", "под", "вы", "от", "а", "не", "как",
     "к", "что",  "это", "они", "наш", "до", "я", "быть", "этот",
     'бы', 'оно', 'ага', "но", "то"] +
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


def cleanup(raw_text):
    return "".join(ch.lower() if ch in good_chars else ' '
                   for ch in raw_text)


def replace(raw_text: str):
    for k, v in replaces.items():
        raw_text = raw_text.replace(k, v)

    return raw_text


def tokenize(raw_text):
    words = replace(cleanup(raw_text))

    return [x for word in m.analyze(words)
            if (x := check_word(word))
            ]


__all__ = ("tokenize", )
