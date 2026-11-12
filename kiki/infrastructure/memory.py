import sqlite3
import datetime as dt
import re
from kiki.domain.text import normalize

class Memory:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, text TEXT NOT NULL, created TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, text TEXT NOT NULL, due TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, alerted INTEGER NOT NULL DEFAULT 0)')
        self.db.commit()

    def save(self, text):
        self.db.execute('INSERT INTO notes(text,created) VALUES (?,?)', (text, dt.datetime.now().isoformat(timespec='seconds')))
        self.db.commit()

    def search(self, query):
        stopwords = {'como', 'qual', 'que', 'para', 'uma', 'com', 'foi', 'dos', 'das', 'sobre', 'resolvi', 'problema'}
        words = set(re.findall(r'\w+', normalize(query))) - stopwords
        rows = self.db.execute('SELECT id,text,created FROM notes ORDER BY id DESC').fetchall()
        if not query.strip():
            return rows[:50]
        scored = [(sum(w in normalize(row[1]) for w in words if len(w) > 1), row) for row in rows]
        return [row for score, row in sorted(scored, key=lambda item: item[0], reverse=True) if score][:20]

    def add_task(self, text, due):
        self.db.execute('INSERT INTO tasks(text,due) VALUES (?,?)', (text, due.isoformat(timespec='minutes')))
        self.db.commit()

    def tasks(self):
        return self.db.execute('SELECT id,text,due FROM tasks WHERE done=0 ORDER BY due').fetchall()

    def finish(self, task_id):
        self.db.execute('UPDATE tasks SET done=1 WHERE id=?', (task_id,))
        self.db.commit()

    def overdue(self):
        return self.db.execute('SELECT id,text,due FROM tasks WHERE done=0 AND alerted=0 AND due<=? ORDER BY due', (dt.datetime.now().isoformat(timespec='minutes'),)).fetchall()

    def acknowledge(self, ids):
        self.db.executemany('UPDATE tasks SET alerted=1 WHERE id=?', [(i,) for i in ids])
        self.db.commit()

    def backup(self, path):
        destination = sqlite3.connect(path)
        try:
            self.db.backup(destination)
        finally:
            destination.close()


