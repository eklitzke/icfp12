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
            color = CELL_TO_COLOR_PAIR.get(cell, curses.color_pair(0))
            screen.addstr(y, x, cell, color)
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
    screen.addstr("Moves:")
    screen.addstr("".join(moves))
    screen.refresh()

KEY_TO_MOVES = {
    curses.KEY_UP: "U",
    curses.KEY_DOWN: "D",
    curses.KEY_LEFT: "L",
    curses.KEY_RIGHT: "R",
}

def translate_key(key):
    return KEY_TO_MOVES[key]

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
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.cbreak()
    curses.noecho()

    screen_y, screen_x = stdscr.getmaxyx()
    control_win = curses.newwin(4, screen_x, 0, 0)

    control_win.keypad(1)
    control_win.timeout(-1)

    control_win.border()
    control_win.refresh()

    world_win = curses.newwin(screen_y - 4, screen_x, 4, 0)
    world_win.border()
    world_win.refresh()

    try:
        while True:
            log.debug("Draw Loop")
            display_moves(control_win, moves)
            draw_world(world_win, my_world)
            c = control_win.getch()
            if c == -1:
                break
            if c in (ord('q'), ord('Q')):
                break
            if c in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
                move = translate_key(c)
                moves.append(move)
                my_world = update_world(move, my_world)
            else:
                log.debug("Unused key, %r", curses.keyname(c))

    finally:
        curses.nocbreak(); stdscr.keypad(0); curses.echo()
        curses.endwin()





if __name__ == "__main__":
    main()
