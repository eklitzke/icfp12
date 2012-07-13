import collections
import fileinput
import logging
import urllib
import urllib2

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

    def clear(self):
        self.rocks.clear()

class WorldEvent(Exception):
    pass

class InvalidMove(WorldEvent):
    pass

class GameOverError(WorldEvent):
    pass


class World(object):
    def __init__(self, robot, map, remaining_lambdas=0, lambdas_collected=0, score=0, moves=''):
        self.robot = robot
        self.moves = moves
        self.map = map
        self.old_moved_rocks = MovedRocks()  # rocks that moved last turn
        self.new_moved_rocks = MovedRocks()  # rocks that moved this turn
        self.remaining_lambdas = remaining_lambdas
        self.lambdas_collected = lambdas_collected
        self.score = score
        self.done = False

    def size(self):
        """Get a tuple of the width and the height of the map"""
        return len(self.map[0]), len(self.map)

    def copy(self):
        """Make a copy of the World object."""
        w = World(self.robot, [row[:] for row in self.map],
                  self.remaining_lambdas, self.lambdas_collected, self.score,
                  self.moves)
        w.old_moved_rocks = self.new_moved_rocks
        return w

    def translate(self, x, y):
        """Translate logical coordinates into actual self.map coordinates."""
        real_y = len(self.map) - y - 1
        real_x = x - 1
        return real_x, real_y

    def at(self, x, y):
        """Get the thing at logical coordinates (x, y)"""
        real_x, real_y = self.translate(x, y)
        #print '(%s, %s) -> (%s, %s)' % (x, y, real_x, real_y)
        try:
            return self.map[real_y][real_x]
        except KeyError:
            return None

    def update_cell(self, x, y, symbol, direction=None):
        """Update a cell with a new symbol. This has some wrapper
        logic to ensure that robot moves are valid, and that rock
        movements are tracked.

        Args:
          x: the x-coordinate of the cell
          y: the y-coordinate of the cell
          symbol: the new symbol to place in the cell
          direction: optional, the direction of movement
        """
        existing = self.at(x, y)
        if symbol == ROCK:
            self.new_moved_rocks.notify(x, y)
        elif symbol == ROBOT:
            if existing == LAMBDA:
                self.remaining_lambdas -= 1
                self.lambdas_collected += 1
                self.score += 25
            elif existing in (EMPTY, EARTH, ROBOT):
                pass
            elif existing == OPEN:
                self.score += 50*self.lambdas_collected
                self.done = True
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
        """Run through all of the rules for a cell at logical
        coordinate (x, y).
        """
        try:
            cell = self.at(x, y)
        except IndexError:
            return None
        if cell == ROBOT:
            pass
        elif cell == ROCK:
            if self.at(x, y - 1) == EMPTY:
                self.update_cell(x, y, EMPTY)
                self.update_cell(x, y - 1, ROCK)
            elif self.at(x, y - 1) == ROBOT and self.old_moved_rocks.moved(x, y):
                self.done = True
                self.score = 0
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
        """Iterate through the logical positions in order of evaluation."""
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
        if self.done:
            raise GameOverError

        world = self.copy()
        world.moves += symbol
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

        world.score -= 1 # should this also happen if you wait?

        if orig_robot_x != robot_x or orig_robot_y != robot_y:
            try:
                world.update_cell(robot_x, robot_y, ROBOT, symbol)
                world.update_cell(orig_robot_x, orig_robot_y, EMPTY)
            except InvalidMove:
                raise

        for x, y in self.positions():
            world.run_cell(x, y)

        if symbol == 'A':
            world.score += 25*world.lambdas_collected
            world.done = True

        return world

    def post_score(self, filename, final_status=None):
        data = {
            'filename': filename,
            'moves': self.moves,
            'score': self.score,
        }
        if final_status:
            data['final_status'] = final_status
        try:
            urllib2.urlopen('http://eklitzke.org/', urllib.urlencode(data), 5)
        except Exception, e:
            pass

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
