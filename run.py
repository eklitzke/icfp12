"A skeleton module for reading standard input"
import argparse
import logging
import world

opt_parser = argparse.ArgumentParser()
opt_parser.add_argument('--verbose', '-v', dest='verbosity', default=0, action='count')
opt_parser.add_argument('files', nargs='*')
log = logging.getLogger('app')
log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s"

def verbosity_to_log_level(verbosity):
    if verbosity >= 2:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.ERROR
    return level

def main():
    args = opt_parser.parse_args()
    logging.basicConfig(level=verbosity_to_log_level(args.verbosity), format=log_fmt)
    log.info('startup')
    w = world.read_world(args.files)
    w.remaining_lambdas = 3
    log.debug('read world: %r', w)
    print w
    print
    for move in 'UUULDDLLUUL':
      w = w.move(move)
      print w
      print

    log.info('shutdown')

if __name__ == "__main__":
    main()
