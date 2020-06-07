import pytest

from time_series import TimeSeries

dates_perc = (
    1586000000,
    1586900000,
    1587000000,
    1587000000,
    1587000000,
    1587100000,
    1587100000,
    1587200000,
    1587300000,
    1587400000,
    1588000000,
)

dates_cut = dates_perc[1:-1]


@pytest.fixture(params=[
    dates_perc, dates_cut
])
def source(request):
    return list(request.param)


def test_max_min():
    ts = TimeSeries('test', dates_perc)
    assert ts.max() == (1587000000, 3)
    assert ts.min() == (1586000000, 1)


def test_create():
    ts = TimeSeries("test", dates_perc)

    assert len(ts.ts) == len(set(dates_perc)) == len(ts.vs)


def test_getitem():
    ts = TimeSeries("test", dates_perc)

    assert len(ts[1586000000:].ts) == len(set(dates_perc))
    assert len(ts[:1588000000].ts) == len(set(dates_perc))


def test_sum(source):
    ts = TimeSeries("test", source)

    assert ts.sum() == ts.vs.sum()


@pytest.mark.parametrize('start', (None, 1500000000, 1586000000, 1586900001))
@pytest.mark.parametrize('stop', (None, 1587300000, 1588000000, 1600000000))
@pytest.mark.parametrize('count', (1, 2, 5, 10))
def test_to_grid(start, stop, count):
    ts = TimeSeries("test", dates_perc)

    sliced = ts[start:stop]
    assert len(sliced.ts)
    assert sliced.sum()

    period = ((stop or sliced.ts.max()) - (start or sliced.ts.min())) / count

    gridded = ts[start:stop:period]

    if start:
        assert gridded.ts.min() == start
    if count != 1 and stop:
        assert gridded.ts.max() == stop

    assert len(gridded.ts) == count
    assert ts[start:stop].sum() == gridded.sum()


def test_cum_sum(source):
    ts = TimeSeries("test", source)

    cs = ts.cumsum()
    assert len(cs.ts) == len(set(source))

    assert cs.vs[-1] == ts.vs.sum()


@pytest.mark.parametrize('x', (0.1, 0.5, 1, 1.1, 10, 100))
def test_div(source, x):
    ts = TimeSeries("test", source)

    assert abs((ts / x).sum() - ts.sum() / x) < 0.001


def test_dist():
    ts1 = TimeSeries('test', dates_perc)
    ts2 = TimeSeries('tost', dates_cut)
    assert ts1.sum() != ts2.sum()
    with pytest.raises(Exception):
        dist = ts1.dist(ts2)
