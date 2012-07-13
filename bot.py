import random
MOVE_COMMANDS = ["U", "D", "L", "R", "A", "W"]

class Bot(object):
    def pick_move(self, the_world):
        return random.choice(MOVE_COMMANDS)
