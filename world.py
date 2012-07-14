import copy
import collections
import hashlib
import fileinput
import logging
import re
import string
import sys
import urllib
import urllib2

log = logging.getLogger('world')

# Map symbols
ROBOT = 'R'
WALL = '#'
LAMBDA = '\\'
ROCK = '*'
CLOSED = 'L'
OPEN = 'O'
EARTH = '.'
EMPTY = ' '
TRAMPOLINES = string.uppercase[:9]
TARGETS = string.digits

# Commands / Directions
LEFT = 'L'
RIGHT = 'R'
UP = 'U'
WAIT = 'W'
DOWN = 'D'
ABORT = 'A'

# States
ABORTED = 'ABORTED'
RUNNING = 'RUNNING'
KILLED = 'KILLED'
FLOODED = 'FLOODED'
REACHED_LIFT = 'REACHED_LIFT'

DEFAULT_FLOODING = 0
DEFAULT_WATER = -1
DEFAULT_WATERPROOF = 10

class WorldEvent(Exception):
    pass

class InvalidMove(WorldEvent):
    pass

class World(object):
    """The world state

    Instance Variables:
    map -- an array of map symbols indexed like [y][x] where (x, y) is bottom left offset coordinate, 0-indexed
    in_lift -- true if we are in the lift false otherwise
    lambdas_collected -- the number of lambdas collected
    num_moves -- the number of moves we have made so far
    remaining_lambdas -- the remaining number of lambdas to be collected
    robot -- the (x, y) offset (from the bottom left) off the robot
    state -- the state of the world.  one of RUNNING, FLOODED, KILLED, ABORTED
    water -- the water level: -1 => no water, 0 => y==0 has water in it, ...
    flooding -- if greater than 0, the number of moves required to increase the water level
    waterproof -- the number of turns the robot may survive in water
    trampolines -- a mapping from a source (x, y) coordinate to a destination (x, y) coordinate where (x, y) is an offset from the bottom left, 0-indexed
    underwater -- the number of moves the robot has made while underwater
    """
    def __init__(self, map,
            in_lift=False,
            lambdas_collected=0,
            num_moves=0,
            remaining_lambdas=None,
            robot=None,
            state=RUNNING,
            water=None,
            flooding=None,
            waterproof=None,
            underwater=0,
            trampolines=None):
        self.in_lift = in_lift
        self.lambdas_collected = lambdas_collected
        self.map = map
        self.num_moves = num_moves
        self.state = state
        if water is None:
            water = DEFAULT_WATER
        self.water = water
        if flooding is None:
            flooding = DEFAULT_FLOODING
        self.flooding = flooding
        if waterproof is None:
            waterproof = DEFAULT_WATERPROOF
        self.waterproof = waterproof
        self.underwater = underwater
        if robot is None:
            # compute the robot position
            for x, y in self.positions():
                if map[y][x] == ROBOT:
                    robot = x, y
                    break
        self.robot = robot # the robot's current position
        if remaining_lambdas is None:
            remaining_lambdas = 0
            # compute the remaining lambdas
            for x, y in self.positions():
                if map[y][x] == LAMBDA:
                    remaining_lambdas += 1
        self.remaining_lambdas = remaining_lambdas
        if trampolines is None:
            trampolines = {}
        self.trampolines = trampolines

    def is_done(self):
        return self.state != RUNNING

    def is_failed(self):
        return self.state == KILLED or self.state == FLOODED

    def is_aborted(self):
        return self.state == ABORTED

    def score(self, force_abort=False):
        if self.is_failed():
            return 0
        if force_abort or self.is_aborted():
            win_mod = 2.0
        else:
            win_mod = 3.0
        return (25 * self.lambdas_collected * win_mod) - self.num_moves

    def size(self):
        """Get a tuple of the width and the height of the map"""
        return len(self.map[0]), len(self.map)

    def key(self):
        return repr((self.map, self.flood_level))

    def copy(self):
        """Make a copy of the World object."""
        return World([row[:] for row in self.map],
                remaining_lambdas=self.remaining_lambdas,
                lambdas_collected=self.lambdas_collected,
                in_lift=self.in_lift,
                state=self.state,
                robot=self.robot,
                num_moves=self.num_moves,
                water=self.water,
                flooding=self.flooding,
                waterproof=self.waterproof,
                underwater=self.underwater,
                trampolines=self.trampolines)

    def at(self, x, y):
        """Get the thing at logical coordinates (x, y)
        0, 0 is the bottom left! forever!
        X -> the left offset
        Y -> the bottom offset
        """
        return self.map[y][x]

    def positions(self):
        """Iterate through the logical positions in order of evaluation."""
        for y in xrange(len(self.map)):
            for x in xrange(len(self.map[y])):
                yield x, y

    def width(self):
        return len(self.map[0])

    def height(self):
        return len(self.map)

    def valid_moves(self):
        """Get the list of valid moves, as a string."""
        ret = ABORT
        w = self.width()
        h = self.height()

        for move in [UP, DOWN, LEFT, RIGHT]:
            dx = 0
            dy = 0
            rx, ry = self.robot
            if move == UP:
                dy += 1
            elif move == DOWN:
                dy -= 1
            elif move == LEFT:
                dx -= 1
            elif move == RIGHT:
                dx += 1
            elif move == WAIT:
                pass
            rx += dx
            ry += dy
            if rx < 0 or ry < 0 or ry >= h or rx >= w:
                continue
            at = self.map[ry][rx]
            if at == WALL:
                continue
            if at == CLOSED:
                continue
            if at in TARGETS:
                continue
            if at == ROCK:
                if dy != 0:
                    continue
                rrx = rx + dx
                rry = ry
                if rry < 0 or rrx < 0 or rry >= h or rrx >= w:
                    continue
                if self.map[rry][rrx] != EMPTY:
                    continue
            ret += move
        return ret

    def _move_robot(self, direction):
        robot_x, robot_y = self.robot
        orig_x, orig_y = self.robot
        dx = 0
        dy = 0
        if direction == UP:
            dy += 1
        elif direction == DOWN:
            dy -= 1
        elif direction == LEFT:
            dx -= 1
        elif direction == RIGHT:
            dx += 1
        elif direction == WAIT:
            pass
        elif direction == ABORT:
            pass
        robot_x += dx
        robot_y += dy
        # this will raise if the new coordinate is outside the map extent
        symbol = self.map[robot_y][robot_x]
        if symbol == ROCK:
           rock_x = robot_x + dx
           rock_y = robot_y + dy
           already_there = self.map[rock_y][rock_x] # this will raise if it's outside the extent
           if already_there != EMPTY:
             raise InvalidMove("unexpected %r" % already_there)
           self.map[rock_y][rock_x] = ROCK
        elif symbol == LAMBDA:
            self.lambdas_collected += 1
            self.remaining_lambdas -= 1
        elif symbol == OPEN:
            self.in_lift = True
        elif symbol == CLOSED:
            raise InvalidMove("unexpected closed lift")
        elif symbol == WALL:
            raise InvalidMove("unexpected wall")
        elif symbol in TARGETS:
            raise InvalidMove("unexpected target")
        elif symbol in TRAMPOLINES:
            target_pos = self.trampolines[robot_x, robot_y]
            # Remove the trampoline target and destination
            self.trampolines = dict((k, v) for (k, v) in self.trampolines.items() if v != target_pos and k != (robot_x, robot_y))
            self.map[robot_y][robot_x] = EMPTY
            robot_x, robot_y = target_pos
        else:
            assert symbol in (EMPTY, EARTH, ROBOT), 'unexpectedly got %r' % (symbol,)
        self.map[orig_y][orig_x] = EMPTY
        self.map[robot_y][robot_x] = ROBOT
        self.robot = robot_x, robot_y
        return self.copy_map(self.map)

    def move(self, direction):
        """Updates the world in place. Generally to make moves, you
        should make a copy of the World() object, move the robot, and
        then call .update() to cause all of the boulders to fall in
        place.
        """
        world = self.copy()

        after_move_map = world._move_robot(direction)
        moved_rocks = set()
        after_update_map = world._update_world(after_move_map, moved_rocks)
        world._check_end(direction, moved_rocks, after_update_map)
        world.map = after_update_map
        world.num_moves += 1
        return world

    def copy_map(self, input_map=None):
        input_map = input_map or self.map
        return copy.deepcopy(input_map)

    def _update_world(self, read_map, moved_rocks):
        logging.info(read_map)
        write_map = self.copy_map(read_map)
        for x, y in self.positions():
            cell = read_map[y][x]
            if cell == ROBOT:
                pass
            elif cell == ROCK:
                below = read_map[y - 1][x]
                left = read_map[y][x - 1]
                right = read_map[y][x + 1]
                rdiag = read_map[y - 1][x + 1]
                ldiag = read_map[y - 1][x - 1]
                if below == EMPTY:
                    write_map[y - 1][x] = ROCK
                    write_map[y][x] = EMPTY
                    moved_rocks.add((x, y - 1))
                # FIXME: what if robot below rock
                elif below == ROCK and right == EMPTY and rdiag == EMPTY:
                    write_map[y][x] = EMPTY
                    write_map[y - 1][x + 1] = ROCK
                    moved_rocks.add((x + 1, y - 1))
                elif below == ROCK and (right != EMPTY or rdiag != EMPTY) and left == EMPTY and ldiag == EMPTY:
                    write_map[y][x] = EMPTY
                    write_map[y - 1][x - 1] = ROCK
                    moved_rocks.add((x - 1, y - 1))
                elif below == LAMBDA and right == EMPTY and rdiag == EMPTY:
                    write_map[y][x] = EMPTY
                    write_map[y - 1][x + 1] = ROCK
                    moved_rocks.add((x + 1, y - 1))
            elif cell == CLOSED and self.remaining_lambdas == 0:
                write_map[y][x] = OPEN
        return write_map

    def _check_end(self, direction, moved_rocks, new_map):
        """Check ending conditions after updating the map"""
        if direction == ABORT:
            self.state = ABORTED
            return
        # Update the underwater count.  Note that we update .underwater before updating .water
        if self.robot[1] <= self.water:
            self.underwater += 1
        else:
            self.underwater = 0
        # Every n-flooding moves, increase the water level
        if self.flooding > 0 and self.num_moves > 0 and (self.num_moves % self.flooding) == 0:
            self.water += 1
        above = self.robot[0], self.robot[1] + 1
        if above in moved_rocks:
            self.state = KILLED
        # If we've been underwater for waterproof turns, we are flooded:
        elif self.underwater > 0 and self.underwater > self.waterproof:
            self.state = FLOODED
        elif self.in_lift:
            self.state = REACHED_LIFT

    def post_score(self, moves, filename, bot_name=None, final_status=None):
        if isinstance(moves, list):
            moves = ''.join(moves)
        data = {
            'filename': filename,
            'moves': moves,
            'score': self.score(),
            'bot_name': bot_name,
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
        return (u'World(robot=%(robot)r, map=%(map)r, in_lift=%(in_lift)r, '
                u'trampolines=%(trampolines)r, water=%(water)r, '
                u'flooding=%(flooding)r, waterproof=%(waterproof)r,'
                u'lambdas_collected=%(lambdas_collected)r, num_moves=%(num_moves)r'
                u' underwater=%(underwater)r)' % self.__dict__)

_ext_pat = re.compile(r"^(.+?)\s+(\d+)$")
# e.g. Trampoline A targets 1
_tramp_pat = re.compile(r"^Trampoline ([A-Za-z]) targets (\d+)$")

def read_world(files):
    """Read a world state from a sequence of files or stdin"""
    width = 0
    height = 0
    a_map = []
    lambdas = 0
    ext = False
    waterproof = None
    water = None
    flooding = None
    trampoline_keys = {}
    for row, line in enumerate(fileinput.input(files)):
        line = line.strip()
        if line == '':
            ext = True
            continue
        elif not ext:
            height = max(height, row + 1)
            row = []
            a_map.append(row)
            for col, char in enumerate(line):
                row.append(char)
                width = max(width, col + 1)
                if char == LAMBDA:
                    lambdas += 1
        else:
            match = _ext_pat.match(line)
            tramp_match = _tramp_pat.match(line)
            if tramp_match:
                trampoline_keys[tramp_match.group(1)] = tramp_match.group(2)
            elif match:
                command = match.group(1).lower()
                val = int(match.group(2))
                if command == "water":
                    # Convert to 0-based index (0 => water at level 0)
                    water = val - 1
                elif command == "flooding":
                    flooding = val
                elif command == "waterproof":
                    waterproof = val
            else:
                log.error("unexpected extension: %r", line)

    # invert the y-axis
    a_map.reverse()
    # pad the map with empties
    for row in a_map:
        for _ in xrange(width - len(row)):
            row.append(EMPTY)
    trampolines = {}
    for src, dst in trampoline_keys.items():
        src_pos = search_map_for_symbol(a_map, src)
        dst_pos = search_map_for_symbol(a_map, dst)
        assert src_pos
        assert dst_pos
        trampolines[src_pos] = dst_pos

    assert len(a_map) == height
    assert len(a_map[0]) == width
    return World(a_map,
            water=water,
            flooding=flooding,
            waterproof=waterproof,
            trampolines=trampolines)

def search_map_for_symbol(a_map, sym):
    "Search the map for a symbol and return the position"
    for y, row in enumerate(a_map):
        for x, c in enumerate(row):
            if c == sym:
                return (x, y)


if __name__ == '__main__':
    world = read_world(sys.argv[1:])
