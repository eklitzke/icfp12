import world
import random
import math

def ucb1_formula(lever_picks, lever_total_reward, total_picks):
    'gives score for a single lever'
    return float(lever_total_reward)/lever_picks + math.sqrt(2.0*math.log(total_picks)/lever_picks)

class Node(object):
    def __init__(self, w, command_history):
        self.world = w
        self.command_history = command_history
        self.unexplored_commands = self.world.valid_commands() # implement. cache of valid commands
        self.child_nodes = {} # map from command character to node
        self.total_picks = 0
        self.total_reward = 0

    def pprint(self, indent=0):
        print '%s[%s] %s reward, %d picks' % (' '*indent, ''.join(self.command_history), self.total_reward, self.total_picks)
        for cmd, child in self.child_nodes.items():
            child.pprint(indent+2)

if __name__ == "__main__":
    initial_world = world.read_world([])
    print initial_world

    tree_root = Node(initial_world, [])

    best_run_score = None
    best_run_commands = None

    while True:
        print '-'*20
        tree_root.pprint()

        ptr = tree_root # start at tree root
        tree_path = [] # record our path down through tree
        command_path = []

        # now walk down from root, doing bandit picks, until we get to a place where we don't have a node yet
        while True:
            tree_path.append(ptr)
            if ptr.unexplored_commands:
                # if there are commands from this point that we haven't tried yet, try one at random
                next_cmd = random.choice(ptr.unexplored_commands)
                ptr.unexplored_commands.remove(next_cmd)
                assert next_cmd not in ptr.child_nodes
                next_world = ptr.world.move(next_cmd)
                new_node = Node(next_world, ptr.command_history+[next_cmd])
                ptr.child_nodes[next_cmd] = new_node
                tree_path.append(new_node)
                command_path.append(next_cmd)
                frontier_world = new_node.world
                break
            else:
                # no unexplored commands from this point, so use bandit algo to pick which child to go to
                if not ptr.child_nodes:
                    print 'NO CHILDREN'
                    print ''.join(command_path)
                scored_cmds = [] # list of (score, cmd) tuples
                for (cmd, child) in ptr.child_nodes.items():
                    scored_cmds.append((ucb1_formula(child.total_picks, child.total_reward, ptr.total_picks), cmd))
                scored_cmds.sort(reverse=True)
                cmd = scored_cmds[0][1]
                ptr = ptr.child_nodes[cmd] # move pointer to best child
                command_path.append(cmd)

        # now we explore on randomly from frontier_world

        #print tree_path

        # now we play a "random" game from this point forward, until end (or maybe some limit)
        depth = 0
        while True:
            if frontier_world.done:
                final_score = frontier_world.score
                break
            elif depth > 100:
                frontier_world.move('A')
                command_path.append('A')
                final_score = frontier_world.score
                break
            else:
                vc = frontier_world.valid_commands()
                cmd = random.choice(vc)
                frontier_world = frontier_world.move(cmd)
                command_path.append(cmd)
                depth += 1

        print 'finished random play with score %s' % final_score
        if best_run_score is None or final_score > best_run_score:
            print 'NEWBEST'
            best_run_score = final_score
            best_run_commands = ''.join(command_path)

        print 'current best %s %s' % (best_run_score, best_run_commands)

        reward = final_score

        # now update all the nodes in the tree that we took to get here
        for node in tree_path:
            node.total_picks += 1
            node.total_reward += reward
