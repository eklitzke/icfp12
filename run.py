"A skeleton module for reading standard input"
import argparse
import fileinput
import logging
import sys

opt_parser = argparse.ArgumentParser()
opt_parser.add_argument('--verbose', '-v', dest='verbosity', default=0, action='count')
opt_parser.add_argument('files', nargs='*')
log = logging.getLogger('app')
log_fmt = u"%(asctime)s %(process)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s"

def on_line(line):
  "Handle a line"
  log.debug('got line: %r', line)

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
  for line in fileinput.input(args.files):
    on_line(line)
  log.info('shutdown')

if __name__ == "__main__":
  main()


