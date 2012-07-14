import optparse
import tornado.ioloop
import tornado.web
import sqlite3

conn = sqlite3.connect('/tmp/scores.db')

def create_table():
    conn.cursor().execute(
        'CREATE TABLE scores ('
        '  id INTEGER PRIMARY KEY,'
        '  filename TEXT NOT NULL,'
        '  score INTEGER NOT NULL,'
        '  moves TEXT NOT NULL,'
        '  final_status TEXT,'
        '  bot_name TEXT)')
    conn.cursor().execute(
        'CREATE INDEX scores_idx ON scores (score, filename)')
    conn.cursor().execute(
        'CREATE INDEX moves_idx ON scores (moves, filename)')

class BaseHandler(tornado.web.RequestHandler):

    columns = ['id', 'filename', 'score', 'moves', 'final_status', 'bot_name']

    @property
    def cursor(self):
        if not hasattr(self, '_cursor'):
            self._cursor = conn.cursor()
            return self._cursor

    def get_scores(self):
         for row in self.cursor.execute(
                'SELECT ' + ', '.join(self.columns) +
                'FROM scores ORDER BY score DESC'):
            yield dict(zip(columns, row))


class MainHandler(BaseHandler):

   def get(self):
       self.set_header('Content-Type', 'text/plain')
       self.write(','.join(self.columns))
       for row in self.get_scores():
           vals = [r[k] for k in self.columns]
           self.write(','.join(vals) + '\n')

    def post(self):
        filename = self.get_argument('filename')
        score = int(self.get_argument('score'))
        moves = self.get_argument('moves')
        final_status = self.get_argument('final_status', None)
        bot_name = self.get_argument('bot_name', None)
        self.cursor.execute(
            'SELECT * FROM scores WHERE filename = ? AND moves = ? LIMIT 1',
            (filename, moves))
        if self.cursor.fetchone() == None:
            self.cursor.execute(
                'INSERT INTO scores (filename, score, moves, final_status, bot_name) '
                'VALUES (?, ?, ?, ?)', (filename, score, moves, final_status, bot_name))
        conn.commit()


if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option('--create-table', action='store_true',
                      help='create the table')
    parser.add_option('--port', type='int', default=9000,
                      help='the port to bind on')
    opts, args = parser.parse_args()

    if opts.create_table:
        create_table()
    else:
        application = tornado.web.Application([
            (r"/", MainHandler),
            ])
        application.listen(opts.port)
        tornado.ioloop.IOLoop.instance().start()
