import random

from word_worker import tokenize


def test_simple():
    text = "Мама мыла раму"

    tokens = tokenize(text)

    assert len(tokens) == 3

    assert tokens[0] == "мама"
    assert tokens[1] == "мыть"
    assert tokens[2] == "рама"


def test_stopwords():
    text = "я как-бы мы оно ага под"

    tokens = tokenize(text)

    assert not tokens


def test_nsu():
    text = "Я учусь в НГУ"

    tokens = tokenize(text)

    assert tokens == ["учиться", "нгу"]


def test_cleanup():
    text = "МаМа мЫлА РаМу"

    wrong_chars = '!,+2=9^>.?}$§%*{/~&<±@:[\\]13456780#_`|'

    new_text = ""

    for ch in text:
        if ch == ' ':
            new_text += random.choice(wrong_chars)
        else:
            new_text += ch

    assert tokenize(text) == tokenize(new_text)


def test_new_line():
    text = "мама\nмыла\nраму"

    x = tokenize(text)
    assert x == ['мама', 'мыть', 'рама']


def test_splitted_word():
    text = "мама:мыла:раму"
    x = tokenize(text)
    assert x == ['мама', 'мыть', 'рама']


def test_none():
    assert [] == tokenize(None)


def test_empty():
    assert [] == tokenize("")
