import world
import random
import math
from heapq import *

def wrc(weighted_choices):
    total_weight = sum(w for (w, c) in weighted_choices)
    x = random.random()*total_weight
    for (w, c) in weighted_choices:
        x -= w
        if x < 0:
            return c
    return c

class AvgEpsilonChooser(object):
    def __init__(self):
        self.choice_stats = {} # maps choice to (count, total, max)

    def choose(self, valid_choices):
        if random.random() < 0.2:
            return random.choice(valid_choices)
        else:
            scored_choices = []
            for c in valid_choices:
                if c in self.choice_stats:
                    (count, total, maximum) = self.choice_stats[c]
                    scored_choices.append((float(total)/count, c))
                else:
                    scored_choices.append((None, c))

            scored_choices.sort(reverse=True)
            if scored_choices[0][0] is None:
                return random.choice(valid_choices)
            else:
                return scored_choices[0][1]

    def feedback(self, choice, score):
        if choice in self.choice_stats:
            count, total, maximum = self.choice_stats[choice]
        else:
            count, total, maximum = 0, 0, None

        count += 1
        total += score
        if maximum is None or score > maximum:
            maximum = score

        self.choice_stats[choice] = (count, total, maximum)

class MaxEpsilonChooser(object):
    def __init__(self):
        self.choice_stats = {} # maps choice to (count, total, max)

    def choose(self, valid_choices):
        if random.random() < 0.5:
            return random.choice(valid_choices)
        else:
            scored_choices = []
            for c in valid_choices:
                if c in self.choice_stats:
                    (count, total, maximum) = self.choice_stats[c]
                    scored_choices.append((maximum, c))
                else:
                    scored_choices.append((None, c))

            scored_choices.sort(reverse=True)
            if scored_choices[0][0] is None:
                return random.choice(valid_choices)
            else:
                return scored_choices[0][1]

    def feedback(self, choice, score):
        if choice in self.choice_stats:
            count, total, maximum = self.choice_stats[choice]
        else:
            count, total, maximum = 0, 0, None

        count += 1
        total += score
        if maximum is None or score > maximum:
            maximum = score

        self.choice_stats[choice] = (count, total, maximum)

if __name__ == "__main__":
    initial_world = world.read_world([])

    best_score = 0
    best_commands = ''

    chooser_factory = AvgEpsilonChooser

    debug_mode = True
    def debug(s):
        if debug_mode:
            print s

    flow = {} # maps ((x, y), (prev_x, prev_y)) to Chooser
    while True:
        # start a random walk
        debug('starting walk')

        w = initial_world
        prev_x, prev_y = None, None
        path_choices = {} # map of ((x, y), (prev_x, prev_y)) to move we made
        command_list = []

        while True:
            # walk another step
            if w.is_done():
                debug('world done')
                break

            valid_moves = list(w.valid_moves())
            valid_moves.remove('A')
            valid_moves.remove('W')

            x, y = w.robot
            #debug('robot at %d, %d' % (x, y))

            transition = ((x, y), (prev_x, prev_y))
            if transition in path_choices:
                debug('repeated transition')
                break # we repeated ourself, so stop the walk

            chooser = flow.get(transition)
            if chooser is None:
                chooser = chooser_factory()
                flow[transition] = chooser

            command = chooser.choose(valid_moves)
            #debug('command %s' % command)

            w = w.move(command)

            path_choices[transition] = command
            command_list.append(command)

            prev_x = x
            prev_y = y

        final_score = w.score()
        command_str = ''.join(command_list)
        debug('finished walk, score %d path [%s]' % (final_score, command_str))
        for trans, command in path_choices.iteritems():
            flow[trans].feedback(command, final_score)
