from typing import Optional, Sequence, Union

import numpy as np


InpT = Union[Sequence, np.ndarray]


class TimeSeries:
    def __init__(self,
                 name: str,
                 ts: InpT,
                 vs: Optional[InpT] = None
                 ):
        self.name = name
        if vs is None:
            self.ts, self.vs = np.unique(ts, return_counts=True)
        else:
            self.ts, self.vs = ts, vs

        assert isinstance(self.ts, np.ndarray)
        assert isinstance(self.vs, np.ndarray)

        assert len(self.ts) == len(self.vs)

    def __getitem__(self, item: slice) -> "TimeSeries":
        start = item.start or self.ts.min()
        stop = item.stop or self.ts.max()

        if item.start or item.stop:
            filter_ = (start <= self.ts) & (self.ts <= stop)
            t, v = self.ts[filter_], self.vs[filter_]
        else:
            t, v = self.ts, self.vs

        if not item.step:
            return TimeSeries(f"{self.name}[sliced]", t, v)

        count = int((stop - start) / item.step) or 1

        xi = np.linspace(start, stop, num=count, dtype=int)
        new_v = np.zeros((len(xi) + 1,), dtype=int)

        indexes = ((t - start) // item.step).round().astype(int)

        np.add.at(new_v, indexes, v)
        new_v[-2] += new_v[-1]

        return TimeSeries(f"{self.name}[sliced#]", xi, new_v[:-1])

    def min(self):
        index = self.vs.argmin()
        return self.ts[index], self.vs[index]

    def max(self):
        index = self.vs.argmax()
        return self.ts[index], self.vs[index]

    def sum(self):
        return self.vs.sum()

    def cumsum(self):
        return TimeSeries(f"∫({self.name})", self.ts, self.vs.cumsum())

    def __truediv__(self, other: float):
        return TimeSeries(f"{self.name} / {other}", self.ts, self.vs / other)

    def dist(self, ts: "TimeSeries"):
        tss = np.unique(np.append(self.ts, ts.ts))
        tss.sort()
        start = tss.min()
        stop = tss.max()
        step = np.percentile(np.diff(tss), 50)
        print("Grid:", start, stop, step)

        self_g = self[start:stop:step]
        ts_g = ts[start:stop:step]

        dist = np.sum((self_g.vs - ts_g.vs) ** 2) ** 0.5
        return dist

