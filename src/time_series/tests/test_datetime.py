import datetime

import pytest

from time_series import TimeSeries


def test_dt():
    dt_from_ = datetime.datetime(2019, 12, 1)
    dt_to_ = datetime.datetime(2020, 1, 1)

    from_ = dt_from_.timestamp()
    to_ = dt_to_.timestamp()

    orig_grid = 10

    ts_raw = [i * orig_grid + from_ for i in range(-2 * orig_grid, int((to_-from_) / orig_grid) + 2 * orig_grid)]

    assert ts_raw

    ts = TimeSeries("test", ts_raw)

    assert ts.ts.min() < from_
    assert ts.ts.max() > to_

    time_interval = datetime.timedelta(days=1)

    assert ts[from_:to_:time_interval.total_seconds()] == ts[dt_from_:dt_to_:time_interval]


def test_eq():
    # generate variant
    variants = [
        [i // 5 for i in range(100 * j, 199 * j)]
        for j in range(1, 5)
    ]

    for one in variants:
        for two in variants:
            if one == two:
                assert TimeSeries('a', one) == TimeSeries('b', two)
            else:
                assert TimeSeries('c', one) != TimeSeries('d', two)

