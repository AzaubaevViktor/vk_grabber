import math
from collections import defaultdict
from typing import List, Optional, Dict

from core import Log


def spline_dist_f(x):
    if 0.5 > x:
        return x
    if x >= 0.5:
        return 1 - x


class Grid:
    def __init__(self, _min, dt):
        self.start = _min
        self.step = dt

    def __getitem__(self, pos: float):
        y = ((pos - self.start) // self.step)
        return y * self.step + self.start

    def right(self, pos):
        return pos + self.step

    def left(self, pos):
        return pos - self.step

    def __contains__(self, item: float):
        return math.modf((item - self.start) / self.step)[0] < 0.001

    def __repr__(self):
        return f"<Grid: {self.start}[{self.step}]>"


class Funcs:
    logger = Log("Funcs")

    @staticmethod
    def eq(grid: Grid, pos):
        yield pos, 1
    eq.__name__ = "⊜"

    @staticmethod
    def simple(grid: Grid, pos):
        yield grid[pos], 1
    simple.__name__ = "dridded"

    @staticmethod
    def divide(grid: Grid, pos):
        left = grid[pos]
        right = grid.right(left)

        yield left, (pos - left) / grid.step
        yield right, (right - pos) / grid.step

    divide.__name__ = "divided"

    @classmethod
    def spline(cls, size):
        if size == 1:
            cls.logger.warning("Do not use spline method with", size=size)

        def _(grid: Grid, pos):
            width = size * grid.step
            half = width / 2

            current = grid[pos - half]
            while True:
                coef = (current - pos) / width + 0.5

                if coef >= 1:
                    break
                elif coef > 0:
                    yield current, spline_dist_f(coef) / size * 4

                current = grid.right(current)

        _.__name__ = f"spline_{size}"
        return _


class TimeSeries:
    def __init__(self, name: str, data: Optional[Dict] = None):
        self.name = name
        self.data = data or defaultdict(float)

    def sort(self):
        x = self.data.keys()
        # corresponding y axis values
        y = self.data.values()

        self.data = dict(sorted(zip(*[x, y])))

    def add(self, timestamp: int, value: float):
        self.data[int(timestamp)] += value

    def sum(self):
        return sum(self.data.values())

    def sampling(self, dt, f=Funcs.eq):
        _min = min(self.data.keys())
        _max = max(self.data.keys())

        new_ts = TimeSeries(f"Sampled[{self.name};{f.__name__}]")

        for ts_, v_ in self.data.items():
            for ts, v in f(Grid(_min, dt), ts_):
                new_ts.add(ts, v * v_)

        return new_ts

    def d(self):
        self.sort()
        new_ts = TimeSeries(self.name + "'")

        for pts, ts, pv, v in self._d():
            new_ts.add((ts + pts) / 2, v - pv)

        return new_ts

    def int(self):
        self.sort()
        new_ts = TimeSeries("∫{" + self.name + "}")
        common = 0

        for ts, v in self.data.items():
            common += v
            new_ts.add(ts, common)

        return new_ts

    def _d(self):
        assert len(self) >= 2

        self.sort()
        prev_ts, prev_v = None, None
        for ts, v in self.data.items():
            if prev_v is not None:
                yield prev_ts, ts, prev_v, v

            prev_ts, prev_v = ts, v

    def mid_value(self):
        assert len(self.data) >= 2
        values = tuple(self.data.values())
        return values[len(values) // 2]

    def max_value(self):
        return max(self.data.values())

    def min_value(self):
        return min(self.data.values())

    def mid_d_ts(self):
        dts_sum = 0
        dts_count = 0

        for pts, ts, pv, v in self._d():
            dts_sum += ts - pts
            dts_count += 1

        return dts_sum / dts_count

    def med_d_ts(self):
        items = [ts - pts for pts, ts, _, _ in self._d()]
        return items[len(items) // 2]

    def __add__(self, other: "TimeSeries"):
        return TimeSeries(f"{self.name} + {other.name}",
                          data={
                              **self.data,
                              **other.data
                          })

    def __iadd__(self, other: "TimeSeries"):
        self.data.update(other.data)
        return self

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"<TimeSeries: {self.name}>"


class TSManager:
    def __init__(self):
        self.tss = {}

    def add(self, word: str, timestamp: int, value: float):
        if word not in self.tss:
            self.tss[word] = TimeSeries(word)
        self.tss[word].add(timestamp, value)

    def sorted_by(self, f) -> List[TimeSeries]:
        return sorted(self.tss.values(), key=f, reverse=True)

    def __getitem__(self, item):
        return self.tss[item]
