import io
import argparse
import sys
import curses
import time
import pprint
import logging

import world
import bot

log = logging.getLogger(__name__)

def draw(screen):
    screen.addstr(0, 5, "hello")
    screen.refresh()
    time.sleep(5)

CELL_TO_COLOR_PAIR = {
    '#': 1,
    '\\': 2,
    '*': 3,
    'R': 4,
    'L': 5,
    'O': 6,
}

def draw_world(screen, the_world):
    screen_y, screen_x = screen.getmaxyx()
    width, height = the_world.size()

    world_map = reversed(the_world.map)

    start_x = max(0, (screen_x / 2) - (width / 2))

    x, y = start_x, 1
    for row in world_map:
        x = start_x
        for cell in row:
            #log.debug('Writing %r to %d,%d', cell, x, y)
            color_num = CELL_TO_COLOR_PAIR.get(cell, 0)
            screen.addstr(y, x, cell, curses.color_pair(color_num))
            x += 1
        y += 1

    screen.move(screen_y-1, screen_x-1)
    screen.refresh()

def update_world(move, the_world):
    log.info("Received move %r", move)
    return the_world.move(move)

def display_moves(screen, moves):
    screen.move(1,1)
    screen.clrtoeol()
    screen.addstr("Moves: ")
    screen.addstr("".join(moves))
    screen.refresh()

def display_status(screen, status):
    screen.move(3,1)
    screen.clrtoeol()
    screen.addstr(status)
    screen.refresh()

def display_score(screen, world):
    screen.move(2,1)
    screen.clrtoeol()
    fmt = 'Score: %3d  Collected: %2d  Water: %2d  Flooding: %2d  Waterproof: %2d  Underwater: %2d'
    s = fmt % (world.score(), world.lambdas_collected, world.water,
            world.flooding, world.waterproof, world.underwater)
    screen.addstr(s)
    screen.refresh()

KEY_TO_MOVE = {
    curses.KEY_UP: "U",
    curses.KEY_DOWN: "D",
    curses.KEY_LEFT: "L",
    curses.KEY_RIGHT: "R",
    ord('a'): "A",
    ord('k'): "U",
    ord('j'): "D",
    ord('h'): "L",
    ord('l'): "R",
    ord('w'): "W",
}

def translate_key(key):
    return KEY_TO_MOVE[key]

def main():
    opt_parser = argparse.ArgumentParser()
    #opt_parser.add_argument('--verbose', '-v', dest='verbosity', default=0, action='count')
    opt_parser.add_argument('file')
    args = opt_parser.parse_args()

    log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, filename="vis.log")
    log.debug("Starting vis")

    my_world = world.read_world(args.file)
    #pprint.pprint(my_world)

    worlds = []
    moves = []

    stdscr = curses.initscr()
    curses.start_color()
    curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(5, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_WHITE)
    curses.cbreak()
    curses.noecho()

    screen_y, screen_x = stdscr.getmaxyx()
    control_win = curses.newwin(5, screen_x, 0, 0)

    control_win.keypad(1)
    control_win.timeout(-1)

    control_win.border()
    control_win.refresh()

    world_win = curses.newwin(screen_y - 5, screen_x, 5, 0)
    world_win.border()
    world_win.refresh()

    the_bot = None
    world_event = None
    try:
        while True:
            log.info(my_world)
            move = None
            display_moves(control_win, moves)
            display_score(control_win, my_world)
            draw_world(world_win, my_world)
            c = control_win.getch()
            if c == -1:
                break
            if c == ord('b'):
                if not the_bot:
                    the_bot = bot.WeightedBot()
                move = the_bot.pick_move(my_world)

            if c in (ord('q'), ord('Q')):
                break
            if c in KEY_TO_MOVE.keys() and not my_world.is_done():
                move = translate_key(c)

            if c == ord('u') and moves:
                my_world = worlds.pop()
                moves.pop()

            if move and move in my_world.valid_moves():
                worlds.append(my_world)

                try:
                    my_world = update_world(move, my_world)
                    moves.append(move)
                except world.InvalidMove:
                    my_world = worlds.pop()
                    display_status(control_win, 'Invalid move')
                    continue

                display_status(control_win, '')
            else:
                log.debug("Unused key, %r", curses.keyname(c))
            if my_world.is_done():
                display_status(control_win, 'done')
                break

    except world.WorldEvent, e:
        world_event = e
    finally:
        curses.nocbreak(); stdscr.keypad(0); curses.echo()
        curses.endwin()
        if world_event is not None:
            print 'ended with event %r' % (e.__class__.__name__,)

    print 'FINAL SCORE: %d' % my_world.score()
    print 'MOVES:', ''.join(moves)
    my_world.post_score(moves, args.file)

if __name__ == "__main__":
    main()
