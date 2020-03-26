from word_woker import tokenize


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
