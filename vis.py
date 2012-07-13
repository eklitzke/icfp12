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
    height = len(world)
    width = max(len(row) for row in world)

    start_x = max(0, 40 - (width / 2))

    x, y = start_x, 3 
    for row in world:
        x = start_x
        for cell in row:
            log.debug('Writing %r to %d,%d', cell, x, y)
            screen.addstr(y, x, cell)
            x += 1
        y += 1

    screen.refresh()
    time.sleep(5)


def main():
    log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_fmt, filename="vis.log")
    log.debug("Starting vis")

    map_load = []
    for line in sys.stdin:
        map_load.append(list(line)[:-1])


    stdscr = curses.initscr()
    try:
        draw_world(stdscr, map_load)
        #draw(stdscr)
    finally:
        curses.endwin()





if __name__ == "__main__":
    main()
