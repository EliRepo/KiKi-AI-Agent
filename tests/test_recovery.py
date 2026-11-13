from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from kiki.infrastructure.memory import Memory
from kiki.infrastructure.recovery import restore_backup_copy
from tests.test_memory_updates import create_legacy


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(self.folder.cleanup)
        self.source = Path(self.folder.name) / 'backup.sqlite3'
        self.destination = Path(self.folder.name) / 'restored.sqlite3'

    def test_recovery_preserves_data_and_original_file(self):
        memory = Memory(':memory:')
        try:
            identifier = memory.save('Ana: recuperação fictícia')
            memory.backup(self.source)
        finally:
            memory.db.close()
        before = self.source.read_bytes()
        self.assertEqual(restore_backup_copy(self.source, self.destination), self.destination)
        restored = Memory(self.destination)
        try:
            self.assertEqual(restored.get_note(identifier).text, 'Ana: recuperação fictícia')
            self.assertIsNone(restored.migration_backup)
        finally:
            restored.db.close()
        self.assertEqual(self.source.read_bytes(), before)

    def test_existing_target_and_original_cannot_be_overwritten(self):
        self.source.write_bytes(b'original fixture')
        self.destination.write_bytes(b'current data fixture')
        with self.assertRaises(FileExistsError):
            restore_backup_copy(self.source, self.destination)
        with self.assertRaises(ValueError):
            restore_backup_copy(self.source, self.source)
        self.assertEqual(self.destination.read_bytes(), b'current data fixture')
        self.assertEqual(self.source.read_bytes(), b'original fixture')

    def test_legacy_backup_is_recovered_then_upgraded_without_touching_source(self):
        create_legacy(self.source)
        before = self.source.read_bytes()
        restore_backup_copy(self.source, self.destination)
        restored = Memory(self.destination)
        try:
            self.assertEqual(restored.get_note(7).text, 'Ana: permissão corrigida')
            self.assertTrue(restored.migration_backup.is_file())
            self.assertEqual(len(restored.tasks()), 1)
        finally:
            restored.db.close()
        self.assertEqual(self.source.read_bytes(), before)

    def test_corrupt_missing_and_future_sources_are_refused(self):
        with self.assertRaises(sqlite3.Error):
            restore_backup_copy(self.source, self.destination)
        self.assertFalse(self.source.exists())
        self.source.write_bytes(b'not a sqlite database')
        with self.assertRaises(sqlite3.Error):
            restore_backup_copy(self.source, self.destination)
        self.source.unlink()
        db = sqlite3.connect(self.source)
        try:
            db.execute('PRAGMA user_version=99')
        finally:
            db.close()
        with self.assertRaisesRegex(ValueError, 'mais nova'):
            restore_backup_copy(self.source, self.destination)
        self.assertFalse(self.destination.exists())

    def test_failed_copy_does_not_leave_a_partial_target(self):
        memory = Memory(':memory:')
        try:
            memory.backup(self.source)
        finally:
            memory.db.close()
        actual_connect = sqlite3.connect
        def connect(path, **kwargs):
            if path == self.destination:
                raise sqlite3.OperationalError('simulated disk failure')
            return actual_connect(path, **kwargs)
        with patch('kiki.infrastructure.recovery.sqlite3.connect', side_effect=connect):
            with self.assertRaises(sqlite3.OperationalError):
                restore_backup_copy(self.source, self.destination)
        self.assertFalse(self.destination.exists())
