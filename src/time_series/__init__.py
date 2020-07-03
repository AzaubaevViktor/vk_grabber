import datetime
from typing import Optional, Sequence, Union

import numpy as np
import scipy as scipy
from scipy.signal import find_peaks

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

    @staticmethod
    def _normalize(t):
        if t is None:
            return t

        if isinstance(t, (int, float, np.int64, np.uint, np.integer, np.float)):
            return t

        if isinstance(t, datetime.datetime):
            return t.timestamp()

        if isinstance(t, datetime.timedelta):
            return t.total_seconds()

        raise TypeError(type(t))

    def __getitem__(self, item: slice) -> "TimeSeries":
        start = self._normalize(item.start or self.ts.min())
        stop = self._normalize(item.stop or self.ts.max())
        step = self._normalize(item.step)

        if item.start or item.stop:
            filter_ = (start <= self.ts) & (self.ts <= stop)
            t, v = self.ts[filter_], self.vs[filter_]
        else:
            t, v = self.ts, self.vs

        if not step:
            return TimeSeries(f"{self.name}[sliced]", t, v)

        count = int((stop - start) / step) or 1

        xi = np.linspace(start, stop, num=count, dtype=int)
        new_v = np.zeros((len(xi) + 1,), dtype=int)

        indexes = ((t - start) // step).round().astype(int)

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
        assert np.array_equal(self.ts, ts.ts), "Need identical grid for dist calculation. Use `.dist_grid`"
        dist = np.sum((self.vs - ts.vs) ** 2) ** 0.5
        return dist

    def dist_grid(self, ts: "TimeSeries"):
        tss = np.unique(np.append(self.ts, ts.ts))
        tss.sort()

        start = tss.min()
        stop = tss.max()
        step = np.percentile(np.diff(tss), 50)
        print("Grid:", start, stop, step)

        self_g = self[start:stop:step]
        ts_g = ts[start:stop:step]

        self_g.dist(ts_g)

    def p(self, percentile: float) -> float:
        assert 0 < percentile < 100
        return np.percentile(self.vs, percentile)

    def locals_max(self):
        indices = find_peaks(self.vs, height=self.p(95))
        return self.ts[indices], self.vs[indices]

    @staticmethod
    def _date(time_stamp):
        return datetime.datetime.utcfromtimestamp(time_stamp).strftime('%Y-%m-%dT%H:%M:%SZ')

    def __len__(self):
        return len(self.ts)

    def __eq__(self, other: "TimeSeries"):
        return np.array_equal(self.ts, other.ts) and np.array_equal(self.vs, other.vs)

    def __repr__(self):
        from_ = self.ts.min()
        to_ = self.ts.max()

        return f"<TimeSeries of `{self.name}` " \
               f"[{self._date(from_)} - {self._date(to_)}] " \
               f"{len(self.ts)} items, " \
               f"∑={self.vs.sum():.2f}" \
               f">"
