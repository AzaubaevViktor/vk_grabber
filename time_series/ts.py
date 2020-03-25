from collections import defaultdict
from typing import List


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

    def __repr__(self):
        return f"<Grid: {self.start}[{self.step}]>"


class Funcs:
    @staticmethod
    def eq(grid: Grid, pos, value):
        yield pos, value
    eq.__name__ = "⊜"

    @staticmethod
    def simple(grid: Grid, pos, value):
        yield grid[pos], value
    simple.__name__ = "dridded"

    @staticmethod
    def divide(grid: Grid, pos, value):
        left = grid[pos]
        right = grid.right(left)

        yield left, value * (pos - left) / grid.step
        yield right, value * (right - pos) / grid.step

    divide.__name__ = "divided"

    @staticmethod
    def spline(SIZE):
        def _(grid: Grid, pos, value):
            width = SIZE * grid.step
            half = width / 2

            current = grid[pos - half]
            while True:
                coef = (current - pos) / width + 0.5

                print("  !! ", current, coef)
                if coef >= 1:
                    break
                elif coef > 0:
                    yield current, spline_dist_f(coef) / SIZE * 4 * value

                current = grid.right(current)

        _.__name__ = f"spline_{SIZE}"
        return _


class TimeSeries:
    def __init__(self, name):
        self.name = name
        self.data = defaultdict(float)

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
            print(ts_, v_, "=>>")
            for ts, v in f(Grid(_min, dt), ts_, v_):
                print("  `->", ts, v)
                new_ts.add(ts, v)

        return new_ts

    def d(self):
        self.sort()
        new_ts = TimeSeries(self.name + "'")

        prev_ts, prev_v = None, None
        for ts, v in self.data.items():
            if prev_v is not None:
                new_ts.add((ts + prev_ts) / 2, v - prev_v)

            prev_ts, prev_v = ts, v

        return new_ts

    def int(self):
        self.sort()
        new_ts = TimeSeries("∫{" + self.name + "}")
        common = 0

        for ts, v in self.data.items():
            common += v
            new_ts.add(ts, common)

        return new_ts

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
