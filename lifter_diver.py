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

def world_to_map_str(w):
    return ''.join(''.join(row) for row in w.map)

class Node(object):
    def __init__(self, parent_node, w, command_history):
        self.parent_node = parent_node
        self.world = w
        self.command_history = command_history
        self.unexplored_commands = list(self.world.valid_moves())
        if 'A' in self.unexplored_commands:
            self.unexplored_commands.remove('A') # safe optimization
        #print 'unexplored_commands', self.unexplored_commands
        self.child_nodes = {} # map from command character to node
        self.score = self.world.score()
        self.max_child_score = self.score

    def pprint(self, indent=0, depth_left=-1):
        print '%s[%s] %d %d %s' % (' '*indent, self.command_history, self.score, self.max_child_score, 'DONE' if self.world.is_done() else '')
        if depth_left == 0:
            return
        for cmd, child in self.child_nodes.items():
            if child:
                child.pprint(indent+2, depth_left-1)
            else:
                print '%s[%s] None' % (' '*(indent+2), self.command_history+cmd)

if __name__ == "__main__":
    initial_world = world.read_world([])

    best_score = 0
    best_commands = ''

    node_count = 0

    map_to_node = {} # key is stringified map, value is node

    debug_mode = False
    def debug(s):
        if debug_mode:
            print s

    def add_node(parent, w, map_str, command_history):
        global node_count, best_score, best_commands

        n = Node(parent, w, command_history)
        if best_score is None or n.score > best_score:
            print 'NEWBEST'
            best_score = n.score
            best_commands = n.command_history
        map_to_node[map_str] = n
        node_count += 1
        # if not w.is_done():
        #     explorable_nodes.append(n)
        #     heappush(explore_heapq, (-n.score, n))
        return n

    def attempt_dive(start):
        cursor = start
        greedy_mode = False
        while True:
            if cursor.world.is_done():
                return None # failed dive

            if random.random() < 0.05:
                greedy_mode = True

            if greedy_mode:
                scored_children = [(c.max_child_score, c) for c in cursor.child_nodes.values() if c]
                if scored_children:
                    scored_children.sort(reverse=True)
                    cursor = scored_children[0][1]
                    continue

            diveable_children = [c for c in cursor.child_nodes.values() if c]
            num_possible_children = len(diveable_children) + len(cursor.unexplored_commands)
            if num_possible_children == 0:
                return None
            if random.random() < (float(len(diveable_children))/num_possible_children):
                cursor = random.choice(diveable_children)
            else:
                break # just stay here and explore one of the unexplored possibilities
        return cursor

    root = add_node(None, initial_world, world_to_map_str(initial_world), '')

    itercount = 0
    while True:
        if debug_mode or ((itercount % 1000) == 0):
            print '%d nodes' % node_count
            print 'best score %d for [%s]' % (best_score, best_commands)
            #root.pprint(indent=0, depth_left=3)
        itercount += 1

        while True:
            dive_result = attempt_dive(root)

            if dive_result:
                debug('dive result [%s]' % dive_result.command_history)
                from_node = dive_result
                break
            debug('dive failed')

        next_command = random.choice(from_node.unexplored_commands)
        from_node.unexplored_commands.remove(next_command)
        debug('  trying command %s from node %s' % (next_command, from_node.command_history))

        assert next_command not in from_node.child_nodes

        next_world = from_node.world.move(next_command)

        # see if next world is already in some node
        next_map_str = world_to_map_str(next_world)
        matched_node = map_to_node.get(next_map_str)
        if matched_node is not None and next_world.num_moves >= matched_node.world.num_moves:
            # this command lead to a map we've already seen, with more moves, so it's useless
            debug('  dominated by [%s]' % matched_node.command_history)
            from_node.child_nodes[next_command] = None # mark this edge as useless
        else:
            # we're going to make a new node
            debug('  adding new node for command %s' % next_command)
            new_node = add_node(from_node, next_world, next_map_str, from_node.command_history+next_command)
            from_node.child_nodes[next_command] = new_node

            # if we outdid another node, need to make its parent point to None instead of it
            if matched_node:
                for c, n in matched_node.parent_node.child_nodes.iteritems():
                    if n is matched_node:
                        debug('reassigning parent [%s] edge %s to be None, outdid by [%s]' % (matched_node.parent_node.command_history, c, new_node.command_history))
                        matched_node.parent_node.child_nodes[c] = None
                        break
                else:
                    assert False, "didn't find it"

            # update max scores up chain as necessary
            ms = new_node.score
            p = new_node.parent_node
            while True:
                if not p or ms <= p.max_child_score:
                    break
                p.max_child_score = ms
                p = p.parent_node

