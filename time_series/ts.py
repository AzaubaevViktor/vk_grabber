from collections import defaultdict
from typing import List


class Funcs:
    @staticmethod
    def eq(_min, dt, pos):
        return pos + 36000

    @staticmethod
    def simple(_min, dt, pos):
        y = ((pos - _min) // dt)
        ts = y * dt + _min
        return ts


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

        for ts_, v in self.data.items():
            ts = f(_min, dt, ts_)
            print(ts_, " => ", ts)
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
