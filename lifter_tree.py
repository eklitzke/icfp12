import world
import random
import math

def world_to_map_str(w):
    return ''.join(''.join(row) for row in w.map)

class Node(object):
    def __init__(self, parent_node, w, command_history):
        self.parent_node = parent_node
        self.world = w
        self.command_history = command_history
        #self.unexplored_commands = list(self.world.valid_moves())
        #print 'unexplored_commands', self.unexplored_commands
        self.child_nodes = {} # map from command character to node
        self.effective_score = self.world.effective_score()

    def pprint(self, indent=0):
        print '%s[%s] %d %s' % (' '*indent, self.command_history, self.effective_score, 'DONE' if self.world.is_done() else '')
        for cmd, child in self.child_nodes.items():
            child.pprint(indent+2)

if __name__ == "__main__":
    initial_world = world.read_world([])

    best_score = 0
    best_commands = ''

    node_count = 0

    explorable_edges = [] # (node, command)
    map_to_node = {} # key is stringified map, value is node
    dominated_node_ids = set()

    def add_node(parent, w, map_str, command_history):
        global node_count, best_score, best_commands

        n = Node(parent, w, command_history)
        if best_score is None or n.effective_score > best_score:
            print 'NEWBEST'
            best_score = n.effective_score
            best_commands = n.command_history
        map_to_node[map_str] = n
        node_count += 1
        if not w.is_done():
            vm = w.valid_moves()
            for c in vm:
                if c != 'A':
                    explorable_edges.append((n, c))
        return n

    root = add_node(None, initial_world, world_to_map_str(initial_world), '')

    while explorable_edges:
        print '%d nodes, %d explorable edges' % (node_count, len(explorable_edges))
        print 'best score %d for [%s]' % (best_score, best_commands)
        #root.pprint()

        # pick next edge to explore
        random.shuffle(explorable_edges)
        while True:
            from_node, next_command = explorable_edges.pop()
            print 'considering edge %s from [%s]' % (next_command, from_node.command_history)
            if id(from_node) not in dominated_node_ids:
                break
            print 'from node was dominated, try again'
        assert next_command not in from_node.child_nodes

        next_world = from_node.world.move(next_command)

        # see if next world is already in some node
        next_map_str = world_to_map_str(next_world)
        matched_node = map_to_node.get(next_map_str)
        if matched_node is not None and next_world.num_moves >= matched_node.world.num_moves:
            # this edge is irrelevant, so don't do anything
            print 'edge was dominated by [%s]' % matched_node.command_history
            pass
        else:
            # we're going to make a new node
            new_node = add_node(from_node, next_world, next_map_str, from_node.command_history+next_command)
            from_node.child_nodes[next_command] = new_node

            # if we outdid another node, need to mark it and all its children as dominated
            if matched_node:
                q = [matched_node]
                while q:
                    n = q.pop()
                    dominated_node_ids.add(id(n))
                    for ch in n.child_nodes.values():
                        q.append(ch)
