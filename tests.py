import unittest
import util

class TestSegments(unittest.TestCase):
    def test(self):
        self.assertEquals(list(util.segments(range(2), 2)), [[0, 1]])

class TestRunningTotal(unittest.TestCase):
    def test(self):
        rt = util.RunningTotal()
        rt.add(1)
        rt.add(3)
        self.assertEquals(rt.total, 4)
        self.assertEquals(rt.n, 2)
        self.assertEquals(rt.mean(), 2)

class TestMax(unittest.TestCase):
    def test(self):
        m = util.Max()
        m.add('s', 1)
        m.add('t', 4)
        m.add('u', 0)
        self.assertEquals(m.score, 4)
        self.assertEquals(m.key, 't')

if __name__ == '__main__':
    unittest.main()

