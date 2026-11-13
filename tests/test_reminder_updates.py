from contextlib import closing
import datetime as dt
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from kiki.infrastructure.memory import Memory
from kiki.infrastructure.migrations import SCHEMA_VERSION

NOW = dt.datetime(2026, 11, 13, 10)


class ReminderUpdateTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(':memory:')
        self.addCleanup(self.memory.db.close)
        self.memory.add_task('Conferir Ana', NOW + dt.timedelta(days=1))

    def test_edit_preserves_identity_resets_alert_and_refuses_stale_changes(self):
        original = self.memory.get_task(1)
        self.memory.acknowledge([1])
        updated = self.memory.update_task(1, 'Conferir Ana e Bruno', NOW + dt.timedelta(days=2),
                                          expected_revision=original.revision, now=NOW)
        self.assertEqual(updated.id, original.id)
        self.assertFalse(updated.alerted)
        self.assertEqual(updated.revision, 2)
        for change in (lambda: self.memory.cancel_task(1, expected_revision=1),
                       lambda: self.memory.finish(1, expected_revision=1),
                       lambda: self.memory.update_task(1, 'Não sobrescrever', NOW + dt.timedelta(days=3),
                                                        expected_revision=1, now=NOW)):
            with self.assertRaises(ValueError):
                change()
        self.assertEqual(self.memory.get_task(1), updated)

    def test_postpone_requires_later_future_date_and_keeps_text(self):
        for due in (NOW, NOW + dt.timedelta(days=1)):
            with self.assertRaises(ValueError):
                self.memory.postpone_task(1, due, expected_revision=1, now=NOW)
        updated = self.memory.postpone_task(1, NOW + dt.timedelta(days=3), expected_revision=1, now=NOW)
        self.assertEqual(updated.text, 'Conferir Ana')
        self.assertEqual(updated.due, NOW + dt.timedelta(days=3))

    def test_cancelled_and_completed_reminders_stay_out_of_alerts_and_edits(self):
        self.memory.cancel_task(1, expected_revision=1)
        self.assertTrue(self.memory.get_task(1).cancelled)
        self.assertEqual(self.memory.tasks(), [])
        self.assertEqual(self.memory.overdue(), [])
        with self.assertRaises(ValueError):
            self.memory.update_task(1, 'Não reativar', NOW + dt.timedelta(days=2), expected_revision=2, now=NOW)
        self.memory.add_task('Outro', NOW + dt.timedelta(days=1))
        self.memory.finish(2, expected_revision=1)
        with self.assertRaises(ValueError):
            self.memory.postpone_task(2, NOW + dt.timedelta(days=3), expected_revision=2, now=NOW)

    def test_new_due_date_can_alert_again_then_cancel_prevents_alert(self):
        due = NOW + dt.timedelta(days=2)
        self.memory.acknowledge([1])
        self.memory.update_task(1, 'Conferir', due, expected_revision=1, now=NOW)
        class Later(dt.datetime):
            @classmethod
            def now(cls):
                return due + dt.timedelta(minutes=1)
        with patch('kiki.infrastructure.memory.dt', SimpleNamespace(datetime=Later)):
            self.assertEqual(len(self.memory.overdue()), 1)
            self.memory.cancel_task(1, expected_revision=2)
            self.assertEqual(self.memory.overdue(), [])

    def test_cancelled_state_survives_backup_and_reopen(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder) / 'backup.sqlite3'
            self.memory.cancel_task(1, expected_revision=1)
            self.memory.backup(path)
            restored = Memory(path)
            try:
                self.assertTrue(restored.get_task(1).cancelled)
                self.assertEqual(restored.tasks(), [])
            finally:
                restored.db.close()

    def test_v3_migration_preserves_fields_and_rolls_back_on_failure(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder) / 'v3.sqlite3'
            with closing(sqlite3.connect(path)) as db, db:
                db.execute('CREATE TABLE notes(id INTEGER PRIMARY KEY AUTOINCREMENT,text TEXT NOT NULL,created TEXT NOT NULL,updated TEXT,revision INTEGER NOT NULL DEFAULT 1)')
                db.execute('CREATE TABLE tasks(id INTEGER PRIMARY KEY,text TEXT NOT NULL,due TEXT NOT NULL,done INTEGER NOT NULL DEFAULT 0,alerted INTEGER NOT NULL DEFAULT 0)')
                db.execute('CREATE TABLE action_receipts(proposal_id TEXT PRIMARY KEY,signature TEXT NOT NULL,note_id INTEGER,task_id INTEGER,executed TEXT NOT NULL)')
                db.execute("INSERT INTO tasks VALUES (7,'Preservar','2026-11-14T10:00',0,1)")
                db.execute('PRAGMA user_version=3')
            def fail(db):
                db.execute('ALTER TABLE tasks ADD COLUMN cancelled INTEGER NOT NULL DEFAULT 0')
                raise sqlite3.OperationalError('simulated failure')
            with patch('kiki.infrastructure.migrations._upgrade_tasks', side_effect=fail):
                with self.assertRaises(sqlite3.OperationalError):
                    Memory(path)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 3)
                self.assertEqual(len(db.execute('PRAGMA table_info(tasks)').fetchall()), 5)
            upgraded = Memory(path)
            try:
                self.assertEqual(upgraded.db.execute('PRAGMA user_version').fetchone()[0], SCHEMA_VERSION)
                task = upgraded.get_task(7)
                self.assertEqual(task.text, 'Preservar')
                self.assertTrue(task.alerted)
                self.assertFalse(task.cancelled)
                self.assertEqual(task.revision, 1)
            finally:
                upgraded.db.close()
