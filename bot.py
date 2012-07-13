import argparse
import types
import random
import logging
import math

MOVE_COMMANDS = ["U", "D", "L", "R", "A", "W"]

log = logging.getLogger(__name__)

class Bot(object):
    def pick_move(self, the_world):
        raise NotImplementedError

class RandomBot(object):
    name = "random"
    def pick_move(self, the_world):
        return random.choice(MOVE_COMMANDS)

def point_distance(p0, p1):
    return math.sqrt((p0[0] - p1[0])**2 + (p0[1] - p1[1])**2)

def nearest_lambda(the_world):
    robot = None
    lambdas = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)

        if cell == 'R':
            robot = (x,y)
        elif cell == '\\':
            lambdas.append((x,y))

    if not lambdas:
        return None, None

    assert robot

    robot_x, robot_y = robot
    closest_lambda = None
    min_distance = 100000
    for lambda_x, lambda_y in lambdas:
        distance = point_distance((lambda_x, lambda_y), (robot_x, robot_y))
        if min_distance > distance:
            min_distance = distance
            closest_lambda = (lambda_x, lambda_y)

    return closest_lambda, (lambda_x - robot_x, lambda_y - robot_y)

def nearest_lift(the_world):
    robot = None
    lambdas = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)

        if cell == 'R':
            robot = (x,y)
        elif cell == 'O':
            door = (x,y)

    assert robot
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

        for move in MOVE_COMMANDS:
            running_weight += custom_weights.get(move, self.DEFAULT_WEIGHT)
            weighted_chooser.append((running_weight, move))

        choice = random.random() * running_weight
        ndx = 0
        while weighted_chooser[ndx][0] < choice:
            ndx +=1

        return weighted_chooser[ndx][1]

def run_bot(bot, base_world, iterations):
    max_score = -100000
    max_moves = None
    best_world = None

    for _ in range(iterations):
        the_world = base_world.copy()
        moves = []
        while not the_world.done:
            next_move = the_bot.pick_move(the_world)
            try:
                the_world = the_world.move(next_move)
                moves.append(next_move)
            except world.InvalidMove:
                continue

        if the_world.score > max_score:
            max_score = the_world.score
            max_moves = moves
            best_world = the_world.copy()

    return best_world, max_score, max_moves

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
    opt_parser.add_argument('--iterations', '-i', dest='iterations', default=1000, type=int)
    opt_parser.add_argument('--name', '-n', dest='name', default="random")
    opt_parser.add_argument('file')
    args = opt_parser.parse_args()

    log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, filename="bot.log")
    log.debug("Starting vis")

    the_bot = bot_for_name(args.name)
    the_world = world.read_world(args.file)

    world, score, moves = run_bot(the_bot, the_world, args.iterations)

    print "Moves: %s" % "".join(moves)
    print "Score: %d" % score
    world.post_score(args.file)
