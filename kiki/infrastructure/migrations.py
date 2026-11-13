"""Transactional schema upgrades; preserve a consistent copy before changing an old file."""
from pathlib import Path
import sqlite3
import uuid

SCHEMA_VERSION = 5
BASE_COLUMNS = {'notes': {'id', 'text', 'created'},
                'tasks': {'id', 'text', 'due', 'done', 'alerted'}}


def _validate_schema(db, version):
    expected = {table: set(columns) for table, columns in BASE_COLUMNS.items()}
    if version >= 2:
        expected['notes'].update({'updated', 'revision'})
    if version >= 3:
        expected['action_receipts'] = {'proposal_id', 'signature', 'note_id', 'task_id', 'executed'}
    if version >= 4:
        expected['tasks'].update({'cancelled', 'revision'})
    if version >= 5:
        expected['conversations'] = {'id', 'title', 'created', 'updated'}
        expected['chat_messages'] = {'id', 'conversation_id', 'role', 'text', 'status', 'sources', 'created'}
    for table, columns in expected.items():
        actual = {row[1] for row in db.execute(f'PRAGMA table_info({table})')}
        if actual != columns:
            raise ValueError('O formato do banco não é compatível. Preserve o arquivo e verifique a versão da KiKi.')
    if version < 2 and db.execute(
        "SELECT 1 FROM sqlite_master WHERE tbl_name='notes' AND type IN ('trigger','index') AND sql IS NOT NULL"
    ).fetchone():
        raise ValueError('O banco contém alterações de estrutura não reconhecidas. Preserve-o antes de atualizar.')


def _upgrade_base(db):
    db.execute('CREATE TABLE IF NOT EXISTS notes(id INTEGER PRIMARY KEY, text TEXT NOT NULL, created TEXT NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS tasks(id INTEGER PRIMARY KEY, text TEXT NOT NULL, due TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, alerted INTEGER NOT NULL DEFAULT 0)')


def _upgrade_notes(db):
    # AUTOINCREMENT prevents a deleted source ID from being assigned to a new note.
    db.execute('CREATE TABLE notes_v2(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, '
               'created TEXT NOT NULL, updated TEXT, revision INTEGER NOT NULL DEFAULT 1)')
    db.execute('INSERT INTO notes_v2(id,text,created) SELECT id,text,created FROM notes')
    db.execute('DROP TABLE notes')
    db.execute('ALTER TABLE notes_v2 RENAME TO notes')


def _upgrade_receipts(db):
    db.execute('CREATE TABLE action_receipts(proposal_id TEXT PRIMARY KEY, signature TEXT NOT NULL, '
               'note_id INTEGER, task_id INTEGER, executed TEXT NOT NULL)')


def _upgrade_tasks(db):
    db.execute('ALTER TABLE tasks ADD COLUMN cancelled INTEGER NOT NULL DEFAULT 0')
    db.execute('ALTER TABLE tasks ADD COLUMN revision INTEGER NOT NULL DEFAULT 1')


def _upgrade_history(db):
    db.execute('CREATE TABLE conversations(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, '
               'created TEXT NOT NULL, updated TEXT NOT NULL)')
    db.execute("CREATE TABLE chat_messages(id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id INTEGER NOT NULL "
               "REFERENCES conversations(id) ON DELETE CASCADE, role TEXT NOT NULL CHECK(role IN ('user','assistant')), "
               "text TEXT NOT NULL, status TEXT NOT NULL, sources TEXT NOT NULL DEFAULT '[]', created TEXT NOT NULL)")
    db.execute('CREATE INDEX chat_messages_conversation ON chat_messages(conversation_id,id)')


def migrate(db):
    version = db.execute('PRAGMA user_version').fetchone()[0]
    if version > SCHEMA_VERSION:
        raise ValueError('Este banco foi criado por uma versão mais nova da KiKi. Atualize o aplicativo para abri-lo.')
    tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if tables or version:
        _validate_schema(db, version)
    if version == SCHEMA_VERSION:
        return None
    backup = None
    source = db.execute('PRAGMA database_list').fetchone()[2]
    if source and tables:
        path = Path(source)
        backup = path.with_name(f'{path.stem}.pre-migration-v{version}-{uuid.uuid4().hex}.sqlite3')
        destination = sqlite3.connect(backup)
        try:
            db.backup(destination)
        finally:
            destination.close()
    try:
        db.execute('BEGIN IMMEDIATE')
        # Another process may have upgraded between the initial check and the lock.
        version = db.execute('PRAGMA user_version').fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError('O banco foi atualizado por outra versão. Reabra com a KiKi mais recente.')
        if version == 0:
            _upgrade_base(db)
            db.execute('PRAGMA user_version=1')
            version = 1
        if version == 1:
            _validate_schema(db, version)
            _upgrade_notes(db)
            db.execute('PRAGMA user_version=2')
            version = 2
        if version == 2:
            _validate_schema(db, version)
            _upgrade_receipts(db)
            db.execute('PRAGMA user_version=3')
            version = 3
        if version == 3:
            _validate_schema(db, version)
            _upgrade_tasks(db)
            db.execute('PRAGMA user_version=4')
            version = 4
        if version == 4:
            _validate_schema(db, version)
            _upgrade_history(db)
            db.execute('PRAGMA user_version=5')
        _validate_schema(db, SCHEMA_VERSION)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return backup
