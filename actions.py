import math

# ===================================
# Route Finding
# ===================================
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
            if block and block not in "#*L123456789" and new not in closed_blocks:
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


# ===================================
# Target Finding Functions
# ===================================
def get_robot(the_world):
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        if cell == 'R':
            robot = (x,y)
    return robot

def all_lambdas(the_world):
    lambdas = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        if cell == '\\':
            lambdas.append((x,y))
    return lambdas

def all_movable_rocks(the_world):
    rocks = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        r = the_world.at(x+1, y)
        l = the_world.at(x-1, y)
        if cell == '*':
            if r == " ":
                rocks.append(((1-x,y), "R"))
            elif l == " ":
                rocks.append(((x+1,y), "L"))
    return rocks

def all_dropable_rocks(the_world):
    rocks = []
    for (x, y) in the_world.positions():
        cell = the_world.at(x, y)
        d = the_world.at(x+1, y-1)
        if cell == '*' and d == ".":
            if the_world.at(x+1, y-1) in ". ":
                rocks.append(((x,y-1), "R"))
            elif the_world.at(x-1, y-1) in ". ":
                rocks.append(((x,y-1), "L"))
    return rocks
    
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
    

# ===================================
# Target Finding Functions
# ===================================
def get_actions(the_world):
    robot = get_robot(the_world)
    
    # No lambdas left, try to exit:
    if the_world.remaining_lambdas == 0:
        target, d = nearest_lift(the_world)
        cmds = find_route(the_world, target, robot)
        if cmds:
            return [(len(cmds), cmds)]
        else:
            return [(1, "A")]

    # Find routes to Lambdas
    lambda_routes = []
    def _manhatten_distance(to):
        return abs(to[0]-robot[0]) + abs(to[1]-robot[1])
    for l in all_lambdas(the_world):
        cmds = find_route(the_world, l, robot)
        if cmds:
            lambda_routes.append((len(cmds), cmds))  # lambda_routes.append((_manhatten_distance(l), cmds))

    # Find routes to moveable Rocks (and move them)
    if not lambda_routes:
        for l,d in all_movable_rocks(the_world):
            cmds = find_route(the_world, l, robot)
            if cmds:
                cmds += d  # Move the rock
                lambda_routes.append((len(cmds), cmds))

    # Find routes to moveable Rocks (and drop them)
    if not lambda_routes:
        for l,d in all_dropable_rocks(the_world):
            cmds = find_route(the_world, l, robot)
            if cmds:
                cmds += d  # Move the rock
                lambda_routes.append((len(cmds), cmds))

    # Abort, nothing we can do
    if not lambda_routes:
        lambda_routes.append((1, "A"))
        
    return sorted(lambda_routes)


