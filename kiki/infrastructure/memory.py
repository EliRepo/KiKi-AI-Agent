import sqlite3
import datetime as dt
import re
from kiki.domain.text import normalize
from kiki.domain.notes import Note, NoteConflictError, NoteNotFoundError, validate_note_text
from kiki.infrastructure.migrations import migrate

class Memory:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        try:
            self.migration_backup = migrate(self.db)
        except Exception:
            self.db.close()
            raise

    def save(self, text):
        text = validate_note_text(text)
        with self.db:
            cursor = self.db.execute('INSERT INTO notes(text,created) VALUES (?,?)',
                                     (text, dt.datetime.now().isoformat(timespec='seconds')))
        return cursor.lastrowid

    def get_note(self, note_id):
        row = self.db.execute('SELECT id,text,created,updated,revision FROM notes WHERE id=?', (note_id,)).fetchone()
        if row is None:
            raise NoteNotFoundError('Esse registro não existe mais. Atualize a lista.')
        return Note(*row)

    def update_note(self, note_id, text, *, expected_revision):
        text = validate_note_text(text)
        with self.db:
            cursor = self.db.execute('UPDATE notes SET text=?, updated=?, revision=revision+1 WHERE id=? AND revision=?',
                                     (text, dt.datetime.now().isoformat(timespec='seconds'), note_id, expected_revision))
            if cursor.rowcount != 1:
                self.get_note(note_id)  # Distinguish a missing record from a changed revision.
                raise NoteConflictError('O registro foi alterado. Reabra-o antes de salvar suas mudanças.')
        return self.get_note(note_id)

    def delete_note(self, note_id, *, expected_revision):
        with self.db:
            cursor = self.db.execute('DELETE FROM notes WHERE id=? AND revision=?', (note_id, expected_revision))
            if cursor.rowcount != 1:
                self.get_note(note_id)
                raise NoteConflictError('O registro foi alterado. Confira a nova versão antes de excluir.')

    def search(self, query):
        stopwords = {'como', 'qual', 'quais', 'que', 'para', 'uma', 'com', 'foi', 'dos', 'das',
                     'sobre', 'resolvi', 'problema', 'fiz', 'fez', 'feito', 'fazer', 'eu', 'voce',
                     'meu', 'minha', 'meus', 'minhas', 'quero', 'saber', 'pode', 'poderia', 'favor'}
        words = set(re.findall(r'\w+', normalize(query))) - stopwords
        if not query.strip():
            return self.db.execute('SELECT id,text,created FROM notes ORDER BY id DESC LIMIT 50').fetchall()
        rows = self.db.execute('SELECT id,text,created FROM notes ORDER BY id DESC').fetchall()
        words = {word for word in words if len(word) > 1}
        scored = [(len(words & set(re.findall(r'\w+', normalize(row[1])))), row) for row in rows]
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


