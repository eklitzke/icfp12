import io
import argparse
import sys
import curses
import time
import pprint
import logging

import world

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

    world_map = the_world.map

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

def display_score(screen, score, collected):
    screen.move(2,1)
    screen.clrtoeol()
    screen.addstr('Score: %d' % score)
    screen.move(2, 12)
    screen.addstr('Collected: %d' % collected)
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
    pprint.pprint(my_world)

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

    world_event = None
    try:
        while True:
            log.debug("Draw Loop")
            display_moves(control_win, moves)
            display_score(control_win, my_world.score, my_world.lambdas_collected)
            draw_world(world_win, my_world)
            c = control_win.getch()
            if c == -1:
                break
            if c in (ord('q'), ord('Q')):
                break
            if c in KEY_TO_MOVE.keys():
                move = translate_key(c)
                moves.append(move)
                try:
                    my_world = update_world(move, my_world)
                except world.InvalidMove:
                    display_status(control_win, 'Invalid move')
                    continue
                display_status(control_win, '')
            else:
                log.debug("Unused key, %r", curses.keyname(c))

    except world.WorldEvent, e:
        world_event = e
    finally:
        curses.nocbreak(); stdscr.keypad(0); curses.echo()
        curses.endwin()
        if world_event is not None:
            print 'ended with event %r' % (e.__class__.__name__,)
        print "%d %s" % (my_world.score, "".join(moves))

if __name__ == "__main__":
    main()
