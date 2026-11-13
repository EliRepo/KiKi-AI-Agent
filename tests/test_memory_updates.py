import sqlite3
from contextlib import closing
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from kiki.domain.notes import NoteConflictError, NoteNotFoundError
from kiki.infrastructure.memory import Memory
from kiki.infrastructure.migrations import SCHEMA_VERSION, migrate


def create_legacy(path, version=0):
    with closing(sqlite3.connect(path)) as db, db:
        db.execute('CREATE TABLE notes(id INTEGER PRIMARY KEY, text TEXT NOT NULL, created TEXT NOT NULL)')
        db.execute('CREATE TABLE tasks(id INTEGER PRIMARY KEY, text TEXT NOT NULL, due TEXT NOT NULL, done INTEGER NOT NULL DEFAULT 0, alerted INTEGER NOT NULL DEFAULT 0)')
        db.execute("INSERT INTO notes VALUES (7,'Ana: permissão corrigida','2026-11-12T10:00:00')")
        db.execute("INSERT INTO tasks VALUES (3,'Conferir Ana','2027-01-01T10:00',0,1)")
        db.execute(f'PRAGMA user_version={version}')


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.folder.cleanup)
        self.path = Path(self.folder.name) / 'memory.sqlite3'

    def test_legacy_upgrade_preserves_data_and_creates_original_backup(self):
        for version in (0, 1):
            with self.subTest(version=version):
                path = self.path.with_name(f'legacy-{version}.sqlite3')
                create_legacy(path, version)
                memory = Memory(path)
                try:
                    backup = memory.migration_backup
                    self.assertTrue(backup.is_file())
                    self.assertEqual(memory.db.execute('PRAGMA user_version').fetchone()[0], SCHEMA_VERSION)
                    self.assertEqual(memory.get_note(7).text, 'Ana: permissão corrigida')
                    self.assertEqual(memory.get_note(7).created, '2026-11-12T10:00:00')
                    self.assertEqual(memory.db.execute('SELECT id,text,due,done,alerted FROM tasks').fetchall(),
                                     [(3, 'Conferir Ana', '2027-01-01T10:00', 0, 1)])
                    with closing(sqlite3.connect(backup)) as old:
                        self.assertEqual(old.execute('PRAGMA user_version').fetchone()[0], version)
                        self.assertEqual(len(old.execute('PRAGMA table_info(notes)').fetchall()), 3)
                        self.assertEqual(old.execute('SELECT id FROM notes').fetchall(), [(7,)])
                finally:
                    memory.db.close()
                reopened = Memory(path)
                try:
                    self.assertIsNone(reopened.migration_backup)
                    self.assertEqual(reopened.get_note(7).revision, 1)
                finally:
                    reopened.db.close()

    def test_upgrade_failure_rolls_back_schema_and_version(self):
        create_legacy(self.path)
        def fail_after_write(db):
            db.execute('ALTER TABLE notes ADD COLUMN should_rollback TEXT')
            raise sqlite3.OperationalError('simulated disk failure')
        with patch('kiki.infrastructure.migrations._upgrade_notes', side_effect=fail_after_write):
            with self.assertRaises(sqlite3.OperationalError):
                Memory(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 0)
            self.assertEqual([row[1] for row in db.execute('PRAGMA table_info(notes)')], ['id', 'text', 'created'])
            self.assertEqual(db.execute('SELECT id,text FROM notes').fetchone(), (7, 'Ana: permissão corrigida'))

    def test_future_schema_is_refused_without_modifying_the_file(self):
        create_legacy(self.path, version=99)
        original = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'mais nova'):
            Memory(self.path)
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(len(list(self.path.parent.iterdir())), 1)

    def test_backup_failure_prevents_migration(self):
        create_legacy(self.path)
        with closing(sqlite3.connect(self.path)) as db:
            with patch('kiki.infrastructure.migrations.sqlite3.connect', side_effect=sqlite3.OperationalError('no space')):
                with self.assertRaises(sqlite3.OperationalError):
                    migrate(db)
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 0)
            self.assertEqual(len(db.execute('PRAGMA table_info(notes)').fetchall()), 3)


class MemoryUpdateTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(':memory:')
        self.addCleanup(self.memory.db.close)

    def test_edit_preserves_identity_and_rejects_stale_writes(self):
        identifier = self.memory.save('Ana: informação antiga')
        before = self.memory.get_note(identifier)
        updated = self.memory.update_note(identifier, "Ana: João corrigiu 'permissão';", expected_revision=before.revision)
        self.assertEqual(updated.id, before.id)
        self.assertEqual(updated.created, before.created)
        self.assertIsNotNone(updated.updated)
        self.assertEqual(updated.revision, before.revision + 1)
        self.assertIn("'permissão'", self.memory.search('Joao')[0][1])
        self.assertEqual(self.memory.search('antiga'), [])
        with self.assertRaises(NoteConflictError):
            self.memory.update_note(identifier, 'Não sobrescrever', expected_revision=before.revision)
        with self.assertRaises(NoteConflictError):
            self.memory.delete_note(identifier, expected_revision=before.revision)
        self.assertEqual(self.memory.get_note(identifier), updated)

    def test_deleted_ids_are_not_reused(self):
        identifier = self.memory.save('Registro fictício')
        self.memory.delete_note(identifier, expected_revision=1)
        self.assertEqual(self.memory.search(''), [])
        self.assertGreater(self.memory.save('Outro registro'), identifier)
        with self.assertRaises(NoteNotFoundError):
            self.memory.get_note(identifier)
        with self.assertRaises(NoteNotFoundError):
            self.memory.delete_note(identifier, expected_revision=1)

    def test_empty_text_is_rejected_without_changing_data(self):
        identifier = self.memory.save('Preservar')
        for text in ('', ' \n ', None):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    self.memory.save(text)
                with self.assertRaises(ValueError):
                    self.memory.update_note(identifier, text, expected_revision=1)
        self.assertEqual(self.memory.get_note(identifier).text, 'Preservar')
        self.assertEqual(len(self.memory.search('')), 1)

    def test_backup_restores_changes_and_keeps_deleted_notes_out(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            backup = Path(folder) / 'backup.sqlite3'
            first = self.memory.save('Ana: antigo')
            second = self.memory.save('Excluir este registro fictício')
            self.memory.update_note(first, 'Ana: corrigido', expected_revision=1)
            self.memory.delete_note(second, expected_revision=1)
            self.memory.backup(backup)
            restored = Memory(backup)
            try:
                self.assertEqual(restored.get_note(first), self.memory.get_note(first))
                self.assertEqual(restored.search('Excluir'), [])
                self.assertGreater(restored.save('Novo após restaurar'), second)
            finally:
                restored.db.close()
