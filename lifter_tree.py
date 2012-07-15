import world
import random
import math
from heapq import *

def world_to_map_str(w):
    return ''.join(''.join(row) for row in w.map)

class Node(object):
    def __init__(self, parent_node, w, command_history):
        self.parent_node = parent_node
        self.world = w
        self.command_history = command_history
        self.unexplored_commands = list(self.world.valid_moves())
        self.unexplored_commands.remove('A') # safe optimization
        #print 'unexplored_commands', self.unexplored_commands
        self.child_nodes = {} # map from command character to node
        self.score = self.world.score()
        self.dominated = False

    def pprint(self, indent=0):
        print '%s[%s] %d %s' % (' '*indent, self.command_history, self.score, 'DONE' if self.world.is_done() else '')
        for cmd, child in self.child_nodes.items():
            child.pprint(indent+2)

if __name__ == "__main__":
    initial_world = world.read_world([])

    best_score = 0
    best_commands = ''

    node_count = 0

    explorable_nodes = []
    explore_heapq = []
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
        if not w.is_done():
            explorable_nodes.append(n)
            heappush(explore_heapq, (-n.score, n))
        return n

    root = add_node(None, initial_world, world_to_map_str(initial_world), '')

    itercount = 0
    while True:
        if debug_mode or ((itercount % 1000) == 0):
            print '%d nodes, %d explorable nodes' % (node_count, len(explorable_nodes))
            print 'best score %d for [%s]' % (best_score, best_commands)
        itercount += 1
        #root.pprint()

        # pick next node to explore
        if random.random() > 0.5:
            tries = 0
            while True:
                if not explorable_nodes:
                    from_node = None
                    break

                debug('random pick')

                from_node = random.choice(explorable_nodes)
                debug('picked node [%s]' % from_node.command_history)

                if from_node.dominated:
                    debug('  node was dominated, ignore')
                elif not from_node.unexplored_commands:
                    debug('  no unexplored commands from this node')
                else:
                    break

                tries += 1
                if tries > 2:
                    # compact
                    pre_len = len(explorable_nodes)
                    explorable_nodes = [n for n in explorable_nodes if (not n.dominated) and (n.unexplored_commands)]
                    debug('compacted explore list from %d to %d' % (pre_len, len(explorable_nodes)))
        else:
            while True:
                if not explore_heapq:
                    from_node = None
                    break

                debug('queue pick')

                _, from_node = explore_heapq[0]
                debug('picked node [%s]' % from_node.command_history)

                if from_node.dominated:
                    debug('  node was dominated, ignore')
                    heappop(explore_heapq) # throw it out so we don't get it again
                elif not from_node.unexplored_commands:
                    debug('  no unexplored commands from this node')
                    heappop(explore_heapq) # throw it out so we don't get it again
                else:
                    break

        # this will happen if we ran out of nodes during compacting
        if not from_node:
            break

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
                matched_node.parent = from_node # who's your daddy now, bitch!
                q = [matched_node]
                while q:
                    n = q.pop()
                    n.dominated = True
                    for ch in n.child_nodes.values():
                        if ch is not None:
                            q.append(ch)
