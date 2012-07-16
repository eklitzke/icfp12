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
        self.dominated = False

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

    root = add_node(None, initial_world, world_to_map_str(initial_world), '')

    cursor = root

    itercount = 0
    while True:
        if debug_mode or ((itercount % 1000) == 0):
            print '%d nodes' % node_count
            print 'best score %d for [%s]' % (best_score, best_commands)
            print 'cursor at [%s]' % cursor.command_history
            root.pprint(indent=0, depth_left=3)
        itercount += 1
        #root.pprint()

        # move cursor randomly until we get to somewhere unexplored
        debug('cursor at [%s]' % cursor.command_history)
        while True:
            weighted_choices = []
            if cursor.parent_node:
                weighted_choices.append((2.0, cursor.parent_node))
            if cursor.unexplored_commands:
                weighted_choices.append((1.0, cursor))
            scored_children = [(c.max_child_score, c) for c in cursor.child_nodes.values() if c]
            #debug('scored_children %s' % scored_children)
            if scored_children:
                scored_children.sort(reverse=True)
                weighted_choices.append((1.0, scored_children[0][1]))
                if len(scored_children) > 1:
                    weighted_choices.append((0.5, random.choice(scored_children[1:])[1]))

            assert weighted_choices
            #debug('choices %s' % ' '.join('%.1f:%s' % (w, c.command_history) for (w, c) in weighted_choices))
            pick = wrc(weighted_choices)
            #debug('moved to [%s]' % pick.command_history)

            if pick == cursor:
                from_node = cursor
                break
            cursor = pick
        debug('cursor moved to [%s]' % cursor.command_history)

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

            # if we outdid another node, need to mark it and all its children as dominated
            if matched_node:
                debug('  marking dominated nodes')
                matched_node.parent = None # who's your daddy now, bitch!
                q = [matched_node]
                while q:
                    n = q.pop()
                    n.dominated = True
                    for ch in n.child_nodes.values():
                        if ch is not None:
                            q.append(ch)

            # update max scores up chain as necessary
            ms = new_node.score
            p = new_node.parent_node
            while True:
                if not p or ms <= p.max_child_score:
                    break
                p.max_child_score = ms
                p = p.parent_node

