import io
import argparse
import sys
import curses
import time
import pprint
import logging

log = logging.getLogger(__name__)

def draw(screen):
    screen.addstr(0, 5, "hello")
    screen.refresh()
    time.sleep(5)

def draw_world(screen, world):
    screen_y, screen_x = screen.getmaxyx()
    height = len(world)
    width = max(len(row) for row in world)

    start_x = max(0, (screen_x / 2) - (width / 2))

    x, y = start_x, 1
    for row in world:
        x = start_x
        for cell in row:
            #log.debug('Writing %r to %d,%d', cell, x, y)
            screen.addstr(y, x, cell)
            x += 1
        y += 1

    screen.move(screen_y-1, screen_x-1)
    screen.refresh()

def update_world(key, world, window=None):
    log.info("Received %r", curses.keyname(key))

    if window:
        window.move(1,1)
        window.clrtoeol()
        window.addstr(curses.keyname(key))
        window.refresh()

    return world

def main():
    opt_parser = argparse.ArgumentParser()
    #opt_parser.add_argument('--verbose', '-v', dest='verbosity', default=0, action='count')
    opt_parser.add_argument('file')
    args = opt_parser.parse_args()

    log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, filename="vis.log")
    log.debug("Starting vis")

    map_load = []
    with io.open(args.file, 'r') as file:
        for line in file:
            map_load.append(list(line)[:-1])


    stdscr = curses.initscr()
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
            draw_world(world_win, map_load)
            c = control_win.getch()
            if c == -1:
                break
            if c in (ord('q'), ord('Q')):
                break
            if c in (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT):
                map_load = update_world(c, map_load, window=control_win)
            else:
                log.debug("Unused key, %r", curses.keyname(c))

    finally:
        curses.nocbreak(); stdscr.keypad(0); curses.echo()
        curses.endwin()





if __name__ == "__main__":
    main()
