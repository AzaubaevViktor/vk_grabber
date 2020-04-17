import pytest

from time_series.ts import Funcs, Grid


@pytest.mark.parametrize(
    'grid, pos', (
            (Grid(1000, 10), 1040),
            (Grid(1000, 10), 1035),
            (Grid(1000, 100), 1035),
            (Grid(1000, 100), 1135),
            (Grid(1000, 1), 1022),
            (Grid(1000, 1), 1022.22222),
            (Grid(1000, 50), 1035),
            (Grid(1000, 1000), 1035),
    )
)
@pytest.mark.parametrize(
    'func', (Funcs.eq, Funcs.simple, Funcs.divide,
             Funcs.spline(2), Funcs.spline(4),
             Funcs.spline(10), Funcs.spline(20),
             Funcs.spline(50), Funcs.spline(100))
)
def test_funcs(grid, pos, func):
    full_sum = 0
    for ts, value in func(grid, pos):
        if func is not Funcs.eq:
            assert ts in grid
        full_sum += value

    assert abs(full_sum - 1) < 0.001


