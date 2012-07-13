import argparse
import random
import logging

MOVE_COMMANDS = ["U", "D", "L", "R", "A", "W"]

log = logging.getLogger(__name__)

class Bot(object):
    def pick_move(self, the_world):
        return random.choice(MOVE_COMMANDS)

def run_bot(bot, base_world, iterations):
    max_score = -100000
    max_moves = None
    best_world = None

    for _ in range(iterations):
        the_world = base_world.copy()
        moves = []
        while True:
            next_move = the_bot.pick_move(the_world)
            try:
                the_world = the_world.move(next_move)
            except (world.Aborted, world.Killed):
                moves.append(next_move)
                break
            except world.InvalidMove:
                continue
            else:
                moves.append(next_move)

        if the_world.score > max_score:
            max_score = the_world.score
            max_moves = moves
            best_world = the_world.copy()

    return best_world, max_score, max_moves

if __name__ == "__main__":
    import world
    opt_parser = argparse.ArgumentParser()
    #opt_parser.add_argument('--verbose', '-v', dest='verbosity', default=0, action='count')
    opt_parser.add_argument('--iterations', '-i', dest='iterations', default=1000, type=int)
    opt_parser.add_argument('file')
    args = opt_parser.parse_args()

    log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, filename="bot.log")
    log.debug("Starting vis")

    the_bot = Bot()
    the_world = world.read_world(args.file)

    world, score, moves = run_bot(the_bot, the_world, args.iterations)

    print "Moves: %s" % "".join(moves)
    print "Score: %d" % score
    world.post_score(args.file)
