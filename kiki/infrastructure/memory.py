import sqlite3
import datetime as dt
import re
import hashlib
import json
from kiki.domain.text import normalize
from kiki.domain.notes import Note, NoteConflictError, NoteNotFoundError, validate_note_text
from kiki.infrastructure.migrations import migrate
from kiki.domain.actions import SaveNote, CreateReminder, ActionResult, validate_actions
from kiki.domain.reminders import Reminder, ReminderNotFoundError

class Memory:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.execute('PRAGMA foreign_keys=ON')
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

    def apply_actions(self, proposal_id, actions, now):
        """Commit approved typed effects and their receipt together, once per ID."""
        validate_actions(actions)
        if not isinstance(proposal_id, str) or not re.fullmatch(r'[0-9a-f]{32}', proposal_id):
            raise ValueError('Identificador de proposta inválido.')
        payload = [{'kind': 'save_note', 'text': action.text} if type(action) is SaveNote else
                   {'kind': 'create_reminder', 'text': action.text, 'due': action.due.isoformat()}
                   for action in actions]
        signature = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
        try:
            self.db.execute('BEGIN IMMEDIATE')
            receipt = self.db.execute('SELECT signature,note_id,task_id FROM action_receipts WHERE proposal_id=?',
                                      (proposal_id,)).fetchone()
            if receipt:
                if receipt[0] != signature:
                    raise ValueError('O ID da proposta já foi usado com outro conteúdo.')
                self.db.commit()
                return ActionResult(receipt[1], receipt[2], replayed=True)
            note_id, task_id = None, None
            for action in actions:
                if type(action) is SaveNote:
                    cursor = self.db.execute('INSERT INTO notes(text,created) VALUES (?,?)',
                                             (action.text, now.isoformat(timespec='seconds')))
                    note_id = cursor.lastrowid
                elif type(action) is CreateReminder:
                    if action.due <= now:
                        raise ValueError('O horário do lembrete já passou. Reenvie o pedido com uma data futura.')
                    cursor = self.db.execute('INSERT INTO tasks(text,due) VALUES (?,?)',
                                             (action.text, action.due.isoformat(timespec='minutes')))
                    task_id = cursor.lastrowid
            self.db.execute('INSERT INTO action_receipts VALUES (?,?,?,?,?)',
                            (proposal_id, signature, note_id, task_id, now.isoformat(timespec='seconds')))
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        return ActionResult(note_id, task_id)

    def tasks(self):
        return self.db.execute('SELECT id,text,due FROM tasks WHERE done=0 AND cancelled=0 ORDER BY due').fetchall()

    def get_task(self, task_id):
        row = self.db.execute('SELECT id,text,due,done,alerted,cancelled,revision FROM tasks WHERE id=?', (task_id,)).fetchone()
        if row is None:
            raise ReminderNotFoundError('Esse lembrete não existe. Atualize a lista.')
        return Reminder(row[0], row[1], dt.datetime.fromisoformat(row[2]), bool(row[3]), bool(row[4]), bool(row[5]), row[6])

    def _check_task_change(self, task_id, cursor):
        if cursor.rowcount != 1:
            self.get_task(task_id)
            raise ValueError('O lembrete mudou, foi concluído ou cancelado. Reabra-o antes de alterar.')

    def update_task(self, task_id, text, due, *, expected_revision, now=None):
        text = validate_note_text(text)
        now = now or dt.datetime.now()
        if not isinstance(due, dt.datetime) or due.tzinfo is not None or due <= now or due.second or due.microsecond:
            raise ValueError('Informe uma data e hora futuras, com precisão de minutos.')
        with self.db:
            cursor = self.db.execute('UPDATE tasks SET text=?,due=?,alerted=0,revision=revision+1 '
                                     'WHERE id=? AND revision=? AND done=0 AND cancelled=0',
                                     (text, due.isoformat(timespec='minutes'), task_id, expected_revision))
            self._check_task_change(task_id, cursor)
        return self.get_task(task_id)

    def postpone_task(self, task_id, due, *, expected_revision, now=None):
        task = self.get_task(task_id)
        if not isinstance(due, dt.datetime) or due.tzinfo is not None or due <= task.due:
            raise ValueError('Para adiar, escolha um horário posterior ao horário atual do lembrete.')
        return self.update_task(task_id, task.text, due, expected_revision=expected_revision, now=now)

    def cancel_task(self, task_id, *, expected_revision):
        with self.db:
            cursor = self.db.execute('UPDATE tasks SET cancelled=1,revision=revision+1 '
                                     'WHERE id=? AND revision=? AND done=0 AND cancelled=0', (task_id, expected_revision))
            self._check_task_change(task_id, cursor)

    def finish(self, task_id, *, expected_revision=None):
        if expected_revision is None:
            expected_revision = self.get_task(task_id).revision
        with self.db:
            cursor = self.db.execute('UPDATE tasks SET done=1,revision=revision+1 '
                                     'WHERE id=? AND revision=? AND done=0 AND cancelled=0', (task_id, expected_revision))
            self._check_task_change(task_id, cursor)

    def overdue(self):
        return self.db.execute('SELECT id,text,due FROM tasks WHERE done=0 AND cancelled=0 AND alerted=0 AND due<=? ORDER BY due', (dt.datetime.now().isoformat(timespec='minutes'),)).fetchall()

    def acknowledge(self, ids):
        self.db.executemany('UPDATE tasks SET alerted=1 WHERE id=? AND done=0 AND cancelled=0', [(i,) for i in ids])
        self.db.commit()

    def backup(self, path):
        destination = sqlite3.connect(path)
        try:
            self.db.backup(destination)
        finally:
            destination.close()

    def conversation_list(self):
        return self.db.execute('SELECT id,title,created,updated FROM conversations ORDER BY updated DESC,id DESC').fetchall()

    def begin_chat_exchange(self, conversation_id, title, text, kind, created):
        with self.db:
            if conversation_id is None:
                cursor = self.db.execute('INSERT INTO conversations(title,created,updated) VALUES (?,?,?)', (title, created, created))
                conversation_id = cursor.lastrowid
            elif not self.db.execute('SELECT 1 FROM conversations WHERE id=?', (conversation_id,)).fetchone():
                raise ValueError('A conversa foi excluída. Abra uma nova conversa.')
            user = self.db.execute('INSERT INTO chat_messages(conversation_id,role,text,status,created) VALUES (?,?,?,?,?)',
                                   (conversation_id, 'user', text, kind, created)).lastrowid
            reply = self.db.execute('INSERT INTO chat_messages(conversation_id,role,text,status,created) VALUES (?,?,?,?,?)',
                                    (conversation_id, 'assistant', 'Aguardando resultado…', 'pending', created)).lastrowid
            self.db.execute('UPDATE conversations SET updated=? WHERE id=?', (created, conversation_id))
        return conversation_id, user, reply

    def complete_chat_message(self, conversation_id, message_id, text, status, sources, updated):
        with self.db:
            cursor = self.db.execute('UPDATE chat_messages SET text=?,status=?,sources=? '
                                     "WHERE id=? AND conversation_id=? AND status='pending'",
                                     (text, status, json.dumps(sources, ensure_ascii=False), message_id, conversation_id))
            if cursor.rowcount != 1:
                raise ValueError('A mensagem já foi concluída ou a conversa foi excluída.')
            self.db.execute('UPDATE conversations SET updated=? WHERE id=?', (updated, conversation_id))

    def conversation_messages(self, conversation_id):
        rows = self.db.execute('SELECT id,role,text,status,sources,created FROM chat_messages '
                               'WHERE conversation_id=? ORDER BY id', (conversation_id,)).fetchall()
        result = []
        for identifier, role, text, status, encoded, created in rows:
            sources = json.loads(encoded)
            if not isinstance(sources, list) or any(not isinstance(row, list) or len(row) != 3 or
                    type(row[0]) is not int or not isinstance(row[1], str) or not isinstance(row[2], str) for row in sources):
                raise ValueError('As fontes desta conversa estão em formato inválido.')
            result.append((identifier, role, text, status, tuple(tuple(row) for row in sources), created))
        return result

    def delete_conversation(self, conversation_id):
        with self.db:
            self.db.execute('DELETE FROM conversations WHERE id=?', (conversation_id,))

    def clear_conversations(self):
        with self.db:
            self.db.execute('DELETE FROM conversations')

    def prune_conversations(self, cutoff):
        with self.db:
            cursor = self.db.execute('DELETE FROM conversations WHERE updated<?', (cutoff,))
        return cursor.rowcount


