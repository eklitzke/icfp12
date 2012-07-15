def segments(xs, n):
    """Get a generic over the segments of a sequence

    xs -- list, this should be a list
    n -- int, the segment length
    """
    assert n > 0
    for i in xrange(0, len(xs), n):
        yield xs[i:i + n]

class RunningTotal(object):
    """Manage a running total"""
    total = 0
    n = 0

    def mean(self):
        if self.n > 0:
            return float(self.total) / self.n

    def add(self, val):
        self.n += 1
        self.total += val

class Max(object):
    """A cell holding the maximum value"""
    key = None
    score = None

    def add(self, key, score):
        if self.score is None:
            self.key = key
            self.score = score
        elif score > self.score:
            self.score = score
            self.key = key

