import collections
import fileinput
import logging

log = logging.getLogger('world')

ROBOT = 'R'
WALL = '#'
LAMBDA = '\\'
ROCK = '*'
CLOSED = 'L'
OPEN = 'O'
EARTH = '.'
EMPTY = ' '

class World(object):
    def __init__(self, robot, map):
        self.robot = robot
        self.map = map

    def size(self):
        "Get a tuple of the width and the height of the map"
        return len(self.map[0]), len(self.map)

    def copy(self):
        return World(self.robot, [row[:] for row in self.map])

    def __repr__(self):
        return u'World(robot=%r, map=%r)' % (self.robot, self.map)

def iterate(world):
    "iterate the world to a new one"
    w = world.copy()
    return w

def read_world(files):
    """Read a world state from a sequence of files or stdin"""
    a_map = collections.defaultdict(lambda: EMPTY)
    width = 0
    height = 0
    a_map = []
    for row, line in enumerate(fileinput.input(files)):
        height = max(height, row + 1)
        row = []
        a_map.append(row)
        for col, char in enumerate(line[:-1]):
            row.append(char)
            width = max(width, col + 1)
    # invert the y-axis
    a_map.reverse()
    # pad the map with empties
    for row in a_map:
        for _ in xrange(width - len(row)):
            row.append(EMPTY)
    robot = (None, None)
    size = (width, height)
    assert len(a_map) == height
    assert len(a_map[0]) == width
    return World(robot, a_map)

if __name__ == '__main__':
    read_world(sys.argv[1:])
