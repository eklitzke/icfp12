import argparse
import types
import random
import logging
import math

MOVE_COMMANDS = ["U", "D", "L", "R", "A", "W"]

log = logging.getLogger(__name__)

def find_route(world, to, origin):
    """Basic A* route finding, to/origin are (x,y) tuples
       world is an instance of World.
    """
    def _manhatten_distance(to):
        return abs(to[0]-origin[0]) + abs(to[1]-origin[1])

    start = tuple(origin)
    open_blocks = {start: (9999,9999,9999,None)}  # FGH
    closed_blocks = {}
    while 1:
        # Get min node:
        current = None
        f_max = 10000000
        for k,v in open_blocks.items():
            if k in closed_blocks:
                continue
            if v[0] < f_max:
                current = k
                f_max = v[0]

#       print "STEP", current, open_blocks.keys(), closed_blocks.keys()
        if current is None:
            # No route!
            return None
            
        #Move current to closed list
        closed_blocks[current] = open_blocks[current]

        # Use it:
        scores = {".": 5, "\\": 0, " ": 2}
        def _think(new):
            block = world.at(new[0], new[1]) 
            if block and block not in "#*" and new not in closed_blocks:
                if new not in open_blocks:
                    h = _manhatten_distance(new)
                    g = scores.get(block, 5)
                    open_blocks[new] = (g+h, g, h, current)
                else:
                    g = scores.get(block, 5)
                    if g < open_blocks[new][1]:
                        h = _manhatten_distance(new) 
                        open_blocks[new] = (g+h, g, h, current)

        _think((current[0], current[1]+1))  # Up
        _think((current[0], current[1]-1))  # Down
        _think((current[0]+1, current[1]))  # Left
        _think((current[0]-1, current[1]))  # Right
                
        if to in closed_blocks:
            break  # Not guarenteed optimal to break on this
 
    # Walk Backwards to get the actual route
    cells = [to]
    previous = closed_blocks[to][3]
    while previous:
        cells.insert(0, previous)
        previous = closed_blocks[previous][3]

    # Output the required robot commands
    last_r = cells[0]
    CMD_STRING = ""
    for r in cells[1:]:
        CMD_STRING += {(1,0):"R", (-1,0):"L", (0,1):"U", (0,-1):"D"}[(r[0]-last_r[0], r[1]-last_r[1])]
        last_r = r
    return CMD_STRING

def get_robot(the_world):
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        if cell == 'R':
            robot = (x,y)
    return robot


def random_lambda(the_world):
    lambdas = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        if cell == '\\':
            lambdas.append((x,y))
    if not lambdas:
        return None
    return random.choice(lambdas)


from actions import get_actions
class NearBot(object):
    name = "nearbot"
    def __init__(self):
        self.route = []

    def pick_move(self, the_world):
        # We have a plan
        robot = get_robot(the_world)
        if the_world.at(robot[0]+1, robot[1]) == "*" and the_world.at(robot[0]+2, robot[1]) == " " and random.random() > 0.6:
            self.route = []
            return "R"

        if the_world.at(robot[0]-1, robot[1]) == "*" and the_world.at(robot[0]-2, robot[1]) == " " and random.random() > 0.6:
            self.route = []
            return "L"

        if self.route:
            return self.route.pop(0)
        
        self.route = list(get_actions(the_world)[0][1])
        return self.route.pop(0)
        # Find the nearest interesting thing and try to get there
        robot = get_robot(the_world)
#        target = random_lambda(the_world)  # Random order
#       target, d = nearest_lambda(the_world) # Nearest by absolute distance, not cmds
        
        target, d = nearest_lambda(the_world)
        if (d and abs(d[0])+abs(d[1]) > 4) and random.random() > 0.5:
            target = random_lambda(the_world)

        if not target:
            target, d = nearest_lift(the_world)

        cmdlist = find_route(the_world, target, robot)
        if cmdlist:
            self.route = list(cmdlist)
            return self.route.pop(0)
        # No Route found, give up
        return "A"

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
    print "Score: %d (%d/%d)" % (score, world.lambdas_collected, world.remaining_lambdas)
    world.post_score(args.file)
