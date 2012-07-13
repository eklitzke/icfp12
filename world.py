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

def not_empty(sym):
    return sym is not None and sym != EMPTY

class MovedRocks(object):

    def __init__(self):
        self.rocks = set()

    def moved(self, x, y):
        """Checks if the rock at x, y moved last turn."""
        return (x, y) in self.rocks

    def notify(self, x, y):
        self.rocks.add((x, y))

class WorldEvent(Exception):
    pass

class InvalidMove(WorldEvent):
    pass

class Killed(WorldEvent):
    pass

class Completed(WorldEvent):
    pass

class Aborted(WorldEvent):
    pass


class World(object):
    def __init__(self, robot, map, remaining_lambdas=0):
        self.robot = robot
        self.map = map
        self.old_moved_rocks = MovedRocks()  # rocks that moved last turn
        self.new_moved_rocks = MovedRocks()  # rocks that moved this turn
        self.remaining_lambdas = remaining_lambdas

    def size(self):
        "Get a tuple of the width and the height of the map"
        return len(self.map[0]), len(self.map)

    def copy(self):
        w = World(self.robot, [row[:] for row in self.map],
                  self.remaining_lambdas)
        return w

    def translate(self, x, y):
      real_y = len(self.map) - y - 1
      real_x = x - 1
      return real_x, real_y

    def at(self, x, y):
        real_x, real_y = self.translate(x, y)
        #print '(%s, %s) -> (%s, %s)' % (x, y, real_x, real_y)
        try:
            return self.map[real_y][real_x]
        except KeyError:
            return None

    def update_cell(self, x, y, symbol, direction=None):
        existing = self.at(x, y)
        if symbol == ROCK:
            self.new_moved_rocks.notify(x, y)
        elif symbol == ROBOT:
            if existing == LAMBDA:
                self.remaining_lambdas -= 1
            elif existing in (EMPTY, EARTH, ROBOT):
                pass
            elif existing == OPEN:
                raise Completed()
            elif existing in (WALL, CLOSED):
                raise InvalidMove()
            elif existing == ROCK:
                if direction == 'L':
                    if self.at(x - 1, y) == EMPTY:
                        self.update_cell(x - 1, y, ROCK)
                    else:
                        raise InvalidMove()
                elif direction == 'R':
                    if self.at(x + 1, y) == EMPTY:
                        self.update_cell(x + 1, y, ROCK)
                    else:
                        raise InvalidMove()
                else:
                    raise InvalidMove()

        real_x, real_y = self.translate(x, y)
        self.map[real_y][real_x] = symbol

    def run_cell(self, x, y):
        try:
            cell = self.at(x, y)
        except IndexError:
            return None
        if cell == ROBOT:
            if self.at(x, y + 1) == ROCK and self.old_moved_rocks.moved(x, y + 1):
                raise Killed()
        elif cell == ROCK:
            if self.at(x, y - 1) == EMPTY:
                self.update_cell(x, y, EMPTY)
                self.update_cell(x, y - 1, ROCK)
            elif (self.at(x, y - 1) == ROCK and self.at(x + 1, y) == EMPTY
                  and self.at(x + 1, y - 1) == EMPTY):
                self.update_cell(x, y, EMPTY)
                self.update_cell(x + 1, y - 1, ROCK)
            elif (self.at(x, y - 1) == ROCK and (not_empty(self.at(x + 1, y)) or not_empty(self.at(x + 1, y - 1))) and self.at(x - 1, y) == EMPTY and self.at(x - 1, y - 1) == EMPTY):
                self.update_cell(x, y, EMPTY)
                self.update_cell(x - 1, y - 1, ROCK)
            elif self.at(x, y -1) == LAMBDA and self.at(x + 1, y) == EMPTY and self.at(x + 1, y - 1) == EMPTY:
                self.update_cell(x, y, EMPTY)
                self.update_cell(x + 1, y - 1, ROCK)
        elif cell == CLOSED:
            if not self.remaining_lambdas:
                self.update_cell(x, y, OPEN)

    def positions(self):
        for row in xrange(1, len(self.map) + 1):
            _, real_y = self.translate(0, row)
            for col in xrange(1, len(self.map[real_y]) + 1):
                yield col, row


    def move(self, symbol):
        """Updates the world in place. Generally to make moves, you
        should make a copy of the World() object, move the robot, and
        then call .update() to cause all of the boulders to fall in
        place.
        """
        if symbol == 'A':
            raise Aborted()
        world = self.copy()
        for x, y in world.positions():
            if world.at(x, y) == ROBOT:
                orig_robot_x = robot_x = x
                orig_robot_y = robot_y = y
        if symbol == 'U':
            robot_y += 1
        elif symbol == 'D':
            robot_y -= 1
        elif symbol == 'L':
            robot_x -= 1
        elif symbol == 'R':
            robot_x += 1

        if orig_robot_x != robot_x or orig_robot_y != robot_y:
            try:
                world.update_cell(robot_x, robot_y, ROBOT, symbol)
                world.update_cell(orig_robot_x, orig_robot_y, EMPTY)
            except InvalidMove:
                pass

        for x, y in self.positions():
            world.run_cell(x, y)

        world.old_moved_rocks = world.new_moved_rocks
        return world

    def __str__(self):
        buf = []
        for row in self.map:
            buf.append(''.join(row))
        buf[-1] += ' %d lambdas left' % (self.remaining_lambdas,)
        return '\n'.join(buf)

    def __repr__(self):
        return u'World(robot=%r, map=%r)' % (self.robot, self.map)

def iterate(world):
    "iterate the world to a new one"
    w = world.copy()
    return w

def read_world(files):
    """Read a world state from a sequence of files or stdin"""
    width = 0
    height = 0
    a_map = []
    lambdas = 0
    for row, line in enumerate(fileinput.input(files)):
        height = max(height, row + 1)
        row = []
        a_map.append(row)
        for col, char in enumerate(line[:-1]):
            row.append(char)
            width = max(width, col + 1)
            if char == LAMBDA:
                lambdas += 1
    # invert the y-axis
    #a_map.reverse()
    # pad the map with empties
    for row in a_map:
        for _ in xrange(width - len(row)):
            row.append(EMPTY)
    robot = (None, None)
    size = (width, height)
    assert len(a_map) == height
    assert len(a_map[0]) == width
    return World(robot, a_map, lambdas)

if __name__ == '__main__':
    world = read_world(sys.argv[1:])
