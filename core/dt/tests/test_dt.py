from time import time

import pytest

from core.dt import Time


@pytest.mark.parametrize(
    'secs, s', (
            (0, "0.0 s"),
            (1, "1.0 s"),
            (59, '59.0 s'),
            (99, '99.0 s'),
            (120, '2.0 m'),
            (150, '2.5 m'),
            (99 * 60, '99.0 m'),
            (100 * 60, '100.0 m'),
            (23 * 60 * 60, '23.0 h'),
            (24 * 60 * 60, '24.0 h'),
            (3.3 * 24 * 60 * 60, '3.3 d')
    )
)
def test_simple(secs, s):
    tm = Time(secs)

    assert s in str(tm)
