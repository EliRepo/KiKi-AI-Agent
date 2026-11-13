import datetime as dt
from pathlib import Path
import tempfile
import unittest
import sqlite3
from contextlib import closing
from unittest.mock import patch
from kiki.application.chat import ChatManager
from kiki.infrastructure.memory import Memory
from kiki.infrastructure.settings import Settings

NOW = dt.datetime(2026, 11, 13, 10)


class ChatTests(unittest.TestCase):
    def test_v4_upgrade_preserves_data_and_failure_rolls_back_with_backup(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder) / 'v4.sqlite3'
            original = Memory(path)
            original.save('Nota preservada')
            original.add_task('Lembrete preservado', NOW + dt.timedelta(days=1))
            with original.db:
                original.db.execute('DROP TABLE chat_messages')
                original.db.execute('DROP TABLE conversations')
                original.db.execute('PRAGMA user_version=4')
            original.db.close()
            def fail(db):
                db.execute('CREATE TABLE conversations(id INTEGER)')
                raise sqlite3.OperationalError('falha fictícia')
            with patch('kiki.infrastructure.migrations._upgrade_history', side_effect=fail):
                with self.assertRaises(sqlite3.OperationalError):
                    Memory(path)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0], 4)
                self.assertIsNone(db.execute("SELECT name FROM sqlite_master WHERE name='conversations'").fetchone())
            self.assertTrue(list(Path(folder).glob('*.pre-migration-v4-*.sqlite3')))
            upgraded = Memory(path)
            try:
                self.assertEqual(upgraded.get_note(1).text, 'Nota preservada')
                self.assertEqual(upgraded.get_task(1).text, 'Lembrete preservado')
                self.assertEqual(upgraded.conversation_list(), [])
                self.assertEqual(upgraded.db.execute('PRAGMA user_version').fetchone()[0], 5)
            finally:
                upgraded.db.close()

    def setUp(self):
        self.memory = Memory(':memory:')
        self.addCleanup(self.memory.db.close)

    def exchange(self, manager, question, answer, status='ok', sources=()):
        key, reply = manager.begin(question)
        manager.complete(key, reply, answer, status, sources)
        return key

    def test_default_chat_is_session_only_and_new_chat_has_no_inherited_messages(self):
        manager = ChatManager(self.memory)
        first = self.exchange(manager, 'Ana?', 'Resposta fictícia')
        self.exchange(manager, 'Mais detalhes?', 'Segunda resposta')
        self.assertEqual(len(manager.current.messages), 4)
        self.assertEqual(self.memory.conversation_list(), [])
        manager.new_chat()
        self.assertEqual(manager.current.messages, [])
        self.assertEqual(manager.context(), [])
        manager.open_chat(first)
        self.assertEqual(len(manager.current.messages), 4)

    def test_opt_in_history_reopens_exact_messages_and_sources(self):
        manager = ChatManager(self.memory, True, 0)
        self.exchange(manager, 'Ana?', 'Permissão [7]', sources=((7, 'Texto enviado', '2026-11-13'),))
        restarted = ChatManager(self.memory)
        key, title, stored = next(row for row in restarted.summaries() if row[2])
        restarted.open_chat(key)
        self.assertEqual(title, 'Ana?')
        self.assertTrue(stored)
        self.assertEqual(restarted.current.messages[-1].sources, ((7, 'Texto enviado', '2026-11-13'),))
        self.assertEqual(restarted.current.messages[-1].text, 'Permissão [7]')

    def test_disabling_history_does_not_append_or_delete_stored_history(self):
        manager = ChatManager(self.memory, True, 0)
        self.exchange(manager, 'Guardar histórico', 'Resposta')
        identifier = manager.current.stored_id
        manager.configure(False, 30)
        self.exchange(manager, 'Temporário', 'Não persistir')
        self.assertEqual(len(self.memory.conversation_messages(identifier)), 2)
        self.assertIsNone(manager.current.stored_id)

    def test_enabling_history_does_not_retroactively_store_temporary_messages(self):
        manager = ChatManager(self.memory)
        self.exchange(manager, 'Mensagem temporária', 'Não gravar')
        manager.configure(True, 0)
        self.exchange(manager, 'A partir de agora', 'Pode gravar')
        rows = self.memory.conversation_messages(manager.current.stored_id)
        self.assertEqual([row[2] for row in rows], ['A partir de agora', 'Pode gravar'])

    def test_retention_and_deletion_leave_notes_tasks_and_receipts_alone(self):
        self.memory.save('Preservar nota fictícia')
        self.memory.add_task('Preservar lembrete', NOW + dt.timedelta(days=1))
        manager = ChatManager(self.memory, True, 0, clock=lambda: NOW - dt.timedelta(days=60))
        self.exchange(manager, 'Histórico antigo', 'Resposta antiga')
        manager.new_chat()
        manager.clock = lambda: NOW
        self.exchange(manager, 'Recente', 'Resposta recente')
        manager.configure(True, 7)
        self.assertEqual(len(self.memory.conversation_list()), 1)
        manager.clear_history()
        self.assertEqual(self.memory.conversation_list(), [])
        self.assertEqual(self.memory.db.execute('SELECT COUNT(*) FROM chat_messages').fetchone()[0], 0)
        self.assertEqual(len(self.memory.search('')), 1)
        self.assertEqual(len(self.memory.tasks()), 1)

    def test_pending_results_block_navigation_and_reject_wrong_request(self):
        manager = ChatManager(self.memory)
        key, reply = manager.begin('Pedido em andamento')
        with self.assertRaises(ValueError):
            manager.new_chat()
        with self.assertRaises(ValueError):
            manager.configure(True, 30)
        with self.assertRaises(ValueError):
            manager.complete('wrong', reply, 'Não inserir')
        manager.complete(key, reply, 'Concluído')
        with self.assertRaises(ValueError):
            manager.complete(key, reply, 'Duplicado')
        self.assertEqual(len(manager.current.messages), 2)

    def test_loaded_pending_action_never_resumes_execution(self):
        manager = ChatManager(self.memory, True, 0)
        manager.begin('Guarde: não executar ao reabrir', kind='action')
        restarted = ChatManager(self.memory)
        key = next(row[0] for row in restarted.summaries() if row[2])
        restarted.open_chat(key)
        self.assertEqual(restarted.current.messages[-1].status, 'interrupted')
        self.assertIn('Confira Memória e Lembretes', restarted.current.messages[-1].text)
        self.assertEqual(self.memory.search(''), [])
        self.assertFalse(restarted.pending)

    def test_context_is_bounded_and_excludes_action_error_and_pending_results(self):
        manager = ChatManager(self.memory)
        for _ in range(10):
            self.exchange(manager, 'x' * 1800, 'y' * 1800)
        context = manager.context()
        self.assertLessEqual(len(context), 6)
        self.assertLessEqual(sum(len(message['content']) for message in context), 3000)
        key, reply = manager.begin('Guarde: comando', kind='action')
        manager.complete(key, reply, 'Erro fictício', 'error')
        self.assertFalse(any('comando' in row['content'] or 'Erro fictício' in row['content'] for row in manager.context()))

    def test_history_and_preferences_survive_database_and_settings_round_trip(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            folder = Path(folder)
            path = folder / 'history.sqlite3'
            memory = Memory(path)
            try:
                self.exchange(ChatManager(memory, True, 0), 'Persistir', 'Resposta')
                Settings(history_enabled=True, history_days=90).save(folder)
            finally:
                memory.db.close()
            reopened = Memory(path)
            try:
                self.assertEqual(len(reopened.conversation_list()), 1)
                self.assertTrue(Settings.load(folder).history_enabled)
                self.assertEqual(Settings.load(folder).history_days, 90)
            finally:
                reopened.db.close()
