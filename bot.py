import argparse
import types
import functools
import random
import logging
import math
import os
import signal
import sys

from actions import get_actions

#MOVE_COMMANDS = ["U", "D", "L", "R", "A", "W"]

log = logging.getLogger(__name__)

def manhattan_distance(origin, to):
    return abs(to[0] - origin[0]) + abs(to[1] - origin[1])

def find_route(a_world, to, origin):
    """Basic A* route finding, to/origin are (x,y) tuples
       world is an instance of World.

       http://en.wikipedia.org/wiki/A*_search_algorithm
    """
    _manhattan_distance = functools.partial(manhattan_distance, origin)

    start = tuple(origin)
    open_blocks = {start: (9999,9999,9999,None)}  # FGH
    closed_blocks = {}
    while True:
        # Get min node:
        current = None
        f_max = 10000000
        for k, v in open_blocks.iteritems():
            if k in closed_blocks:
                continue
            if v[0] < f_max:
                current = k
                f_max = v[0]

#       print "STEP", current, open_blocks.keys(), closed_blocks.keys()
        if current is None:
            # No route!
            return None

        # Move current to closed list
        closed_blocks[current] = open_blocks[current]

        # Use it:
        scores = {world.EARTH: 4, world.LAMBDA: 0, world.EMPTY: 2}
        def _think(new, down=False):
            try:
                block = a_world.at(new[0], new[1])
                safe_to_go_down = True
                if down and a_world.at(new[0], new[1]+2) == world.ROCK:
                    # Down is not an option if there is a rock above us
                    return
            except IndexError:
                # we tried to think of a position that was out-of-bounds
                return
            if block and block not in "#*L123456789" and new not in closed_blocks:
                if new not in open_blocks:
                    h = _manhattan_distance(new)
                    g = scores.get(block, 5)
                    open_blocks[new] = (g+h, g, h, current)
                else:
                    g = scores.get(block, 5)
                    if g < open_blocks[new][1]:
                        h = _manhattan_distance(new)
                        open_blocks[new] = (g+h, g, h, current)

        _think((current[0], current[1]+1))  # Up
        _think((current[0], current[1]-1), True)  # Down
        _think((current[0]+1, current[1]))  # Left
        _think((current[0]-1, current[1]))  # Right

        if to in closed_blocks:
            break  # Not guaranteed optimal to break on this

    # Walk Backwards to get the actual route
    cells = [to]
    previous = closed_blocks[to][3]
    while previous:
        cells.insert(0, previous)
        previous = closed_blocks[previous][3]

    # Output the required robot commands
    last_r = cells[0]
    cmd_string = ""
    for r in cells[1:]:
        cmd_string += {(1,0):world.RIGHT, (-1,0): world.LEFT, (0,1): world.UP, (0,-1): world.DOWN}[(r[0]-last_r[0], r[1]-last_r[1])]
        last_r = r
    return cmd_string

def get_robot(the_world):
    return the_world.robot

def random_lambda(the_world):
    lambdas = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        if cell == '\\':
            lambdas.append((x,y))
    if not lambdas:
        return None
    return random.choice(lambdas)


class NearBot(object):

    name = "nearbot"

    def get_choices(self, the_world):
        """Returns a list of possible moves.

        Returns:
          [(movements, weight)]
        """
        assert not the_world.is_failed() and not the_world.is_done()
        robot = get_robot(the_world)

        choices = []
        # If we can push a rock to the right, add that as a choice.
        if the_world.at(robot[0]+1, robot[1]) == world.ROCK and the_world.at(robot[0]+2, robot[1]) == world.EMPTY:
            choices.append(('R', 1))

        # Same, pushing a rock left
        if the_world.at(robot[0]-1, robot[1]) == world.ROCK and the_world.at(robot[0]-2, robot[1]) == world.EMPTY:
            choices.append(('L', 1))

        # Find the nearest interesting thing and try to get there
        robot = get_robot(the_world)
        num_nearby_lambdas = 5

        # Find the nearest lambdas
        dist_lambdas = nearest_lambdas(the_world)[:num_nearby_lambdas]
        if dist_lambdas:
            closest_distance = dist_lambdas[0][0]
            for dist, lambda_ in dist_lambdas:
                cmdlist = find_route(the_world, lambda_, robot)
                if not cmdlist:
                    continue
                choices.append((cmdlist, float(closest_distance) / len(cmdlist)))

        # There are no lambdas, go to the lift
        else:
            target, d = nearest_lift(the_world)
            choices.append((find_route(the_world, target, robot), 10))

        # No Route found, give up
        if not choices:
            choices.append((world.ABORT, 10))

        return [(route, score * the_world.goodness(extra_moves=len(route)))
                for route, score in choices if route is not None]

class Bot(object):
    def pick_move(self, the_world):
        raise NotImplementedError

class RandomBot(object):
    name = "random"

    def get_choices(self, a_world):
        return [(c, a_world.move(c).goodness()) for c in a_world.valid_moves()]

def point_distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

def nearest_lambdas(the_world):
    """Find the nearest lambda, and the distance to it.

    Returns:
      (closest_lambda, distance)
      closest_lambda -> (x, y) of the lambda
      distance -> (x_distance, y_distance)
    """
    lambdas = []
    for y, row in enumerate(the_world.map):
        for x, c in enumerate(row):
            if c == world.LAMBDA:
                lambdas.append((manhattan_distance(the_world.robot, (x, y)), (x, y)))
    lambdas.sort()
    return lambdas

def nearest_lift(the_world):
    robot = the_world.robot
    lambdas = []
    door = None
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        if cell == 'O':
            door = (x,y)
        elif cell == '\\':
            assert False, 'cannot find open door when lambdas exist'

    assert door

    distance = point_distance(door, robot)
    return door, (door[0] - robot[0], door[1] - robot[1])

class WeightedBot(Bot):
    name = "weighted"

    DEFAULT_WEIGHT = 1.0
    WEIGHTS = {'W': 0.5, 'A': 0.10}
    def pick_move(self, the_world):
        running_weight = 0
        weighted_chooser = []

        custom_weights = self.WEIGHTS.copy()

        l, distance = nearest_lambda(the_world)
        if not l:
            # We should head for the door
            l, distance = nearest_lift(the_world)

        for move in ('L', 'R', 'U', 'D'):
            custom_weights.setdefault(move, self.DEFAULT_WEIGHT)
        if distance[0] < 0:
            custom_weights['L'] += 0.25
        elif distance[0] > 0:
            custom_weights['R'] += 0.25
        else:
            custom_weights['L'] -= 0.25
            custom_weights['R'] -= 0.25

        if distance[1] < 0:
            custom_weights['D'] += 0.25
        elif distance[1] > 0:
            custom_weights['U'] += 0.25
        else:
            custom_weights['D'] -= 0.25
            custom_weights['U'] -= 0.25

        for move in the_world.valid_moves():
            running_weight += custom_weights.get(move, self.DEFAULT_WEIGHT)
            weighted_chooser.append((running_weight, move))

        choice = random.random() * running_weight
        ndx = 0
        while weighted_chooser[ndx][0] < choice:
            ndx +=1

        return weighted_chooser[ndx][1]

def run_path(a_world, path):
    for movement in path:
        if a_world.is_failed():
            return
        try:
            a_world = a_world.move(movement)
        except world.InvalidMove:
            return
    if a_world.is_failed():
        return
    return a_world

class Planner(object):
    def __init__(self):
        self.plans = []

    def add_plan(self, score, plan, world):
        self.plans.append((score, plan, world))

    def pop_plan(self):
        n = sum(i[0] for i in self.plans)
        n *= random.random()
        item = None
        picked = False
        idx = None
        for idx, item in enumerate(self.plans):
            n -= item[0]
            if n <= 0:
                picked = True
                break
        if picked:
            del self.plans[idx]
        return item

    def __len__(self):
        return len(self.plans)

def run_bot(bot, base_world, iterations, on_finish, initial_path=None):

    max_score = -1000
    max_moves = None
    best_world = None
    is_done = False

    def return_best(*args):
        on_finish(best_world, max_score, max_moves)

    signal.signal(signal.SIGINT, return_best)
    signal.signal(signal.SIGALRM, return_best)

    def forever():
        while True:
            yield

    if iterations > 0:
        looper = xrange(iterations)
    else:
        looper = forever()

    planner = Planner()
    if initial_path:
        planner.add_plan(1.0, initial_path, base_world)
    else:
        for plan, weight in bot.get_choices(base_world):
            planner.add_plan(weight, plan, base_world)

    for _ in looper:
        print '\nLOOPING, so far best route is %s %s' % (max_score, max_moves)
        plan = planner.pop_plan()
        if plan is None:
            break
        score, path, a_world = plan
        a_world = run_path(a_world, path)
        if a_world is None:
            continue
        if not (a_world.is_failed() or a_world.is_done()):
            for path, score in bot.get_choices(a_world):
                planner.add_plan(score, path, a_world)

        if a_world.is_done() and a_world.score() > max_score:
            max_score = a_world.score()
            max_moves = a_world.path
            best_world = a_world.copy()
            is_done = True
            print str(a_world)
        elif not a_world.is_done() and a_world.score() > max_score:
            max_score = a_world.score()
            max_moves = a_world.path + 'A'
            best_world = a_world.copy()
            is_done = False
            print str(a_world)

    print ''
    print 'Ran out of iterations!'
    print ''
    on_finish(best_world, max_score, max_moves)

def bot_for_name(name):
    for cls in globals().values():
        if type(cls) == type and getattr(cls, 'name', None) == name:
            return cls()
    else:
        raise AttributeError(name)

if __name__ == "__main__":
    import world
    opt_parser = argparse.ArgumentParser()
    #opt_parser.add_argument('--verbose', '-v', dest='verbosity', default=0, action='count')
    opt_parser.add_argument('--iterations', '-i', dest='iterations', default=None, type=int)
    opt_parser.add_argument('--name', '-n', dest='name', default="random")
    opt_parser.add_argument('--time-based', default=0, type=int, help='max seconds to run')
    opt_parser.add_argument('--initial-path', default='')

    opt_parser.add_argument('file')
    args = opt_parser.parse_args()

    log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, filename="bot.log")
    log.debug("Starting vis")

    the_bot = bot_for_name(args.name)
    the_world = world.read_world(args.file)

    if args.time_based > 0:
        signal.alarm(args.time_based)
        def on_finish(world, score, moves):
            print ''.join(moves)
            sys.exit(0)
        run_bot(the_bot, the_world, -1, on_finish)
    else:
        def on_finish(world, score, moves):
            print "Moves: %s" % "".join(moves)
            print "Score: %d (%d/%d)" % (score, world.lambdas_collected, world.remaining_lambdas)
            world.post_score(moves, args.file, args.name)
            sys.exit(0)
        run_bot(the_bot, the_world, args.iterations, on_finish, initial_path=args.initial_path.rstrip('A'))
