from collections import defaultdict
from typing import List


class Funcs:
    @staticmethod
    def eq(_min, dt, pos, value):
        yield pos + 36000, value

    @staticmethod
    def simple(_min, dt, pos, value):
        y = ((pos - _min) // dt)
        ts = y * dt + _min
        yield ts, value

    @staticmethod
    def divide(_min, dt, pos, value):
        y = ((pos - _min) // dt)
        ts1 = y * dt + _min
        ts2 = ts1 + dt

        yield ts1, value * (pos - ts1) / dt
        yield ts2, value * (ts2 - pos) / dt


class TimeSeries:
    def __init__(self, name):
        self.name = name
        self.data = defaultdict(float)

    def add(self, timestamp: int, value: float):
        self.data[int(timestamp)] += value

    def sum(self):
        return sum(self.data.values())

    def sampling(self, dt, f=Funcs.eq):
        _min = min(self.data.keys())
        _max = max(self.data.keys())

        new_ts = TimeSeries(self.name + "_spline")

        for ts_, v_ in self.data.items():
            print(ts_, v_, "=>>")
            for ts, v in f(_min, dt, ts_, v_):
                print("  `->", ts, v)
                new_ts.add(ts, v)

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
