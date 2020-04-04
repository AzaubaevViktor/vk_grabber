from graph import Link


class NameLink(Link):
    pass


def test_single_label():
    assert "NAME_LINK" in NameLink.labels()
    assert "NAME_LINK" == NameLink.labels()



class TwoLinkXX(NameLink):
    pass


def test_two_label():
    assert "NAME_LINK" in TwoLinkXX.labels()
    assert "TWO_LINK_X_X" in TwoLinkXX.labels()
