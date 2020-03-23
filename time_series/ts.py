from collections import defaultdict
from typing import List


class TimeSeries:
    def __init__(self, name):
        self.name = name
        self.data = defaultdict(float)

    def add(self, timestamp: int, value: float):
        self.data[int(timestamp)] += value

    def sum(self):
        return sum(self.data.values())

    def do_spline(self, dt):
        _min = min(self.data.keys())
        _max = max(self.data.keys())

        new_ts = TimeSeries(self.name + "_spline")

        for ts_, v in self.data.items():
            y = ((ts_ - _min) // dt)
            ts = y * dt + _min
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
