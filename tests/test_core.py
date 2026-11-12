import datetime as dt
import uuid
from contextlib import contextmanager
import unittest
import io
import json
from unittest.mock import patch
from pathlib import Path
from kiki.infrastructure.memory import Memory
from kiki.domain.reminders import parse_reminder
from kiki.infrastructure.ollama import ask_ollama


@contextmanager
def database_file():
    path = Path.cwd() / ('test-' + uuid.uuid4().hex + '.sqlite3')
    try:
        yield path
    finally:
        path.unlink(missing_ok=True)


class MemoryTests(unittest.TestCase):
    def test_explicit_dates_and_missing_time(self):
        now = dt.datetime(2026, 11, 12, 16, 0)
        self.assertEqual(parse_reminder('Conferir Ana amanhã às 10h', now), dt.datetime(2026, 11, 13, 10))
        self.assertEqual(parse_reminder('hoje às 17:30', now), dt.datetime(2026, 11, 12, 17, 30))
        self.assertEqual(parse_reminder('15/11/2026 às 9h15', now), dt.datetime(2026, 11, 15, 9, 15))
        for text in ['amanhã', 'às 10h', 'hoje às 10h', 'amanhã às 25h', '31/02/2027 às 10h']:
            with self.assertRaises(ValueError):
                parse_reminder(text, now)

    def test_backup_and_accent_insensitive_search(self):
        with database_file() as path, database_file() as backup:
            memory = Memory(path)
            memory.save('João corrigiu a permissão.')
            self.assertEqual(len(memory.search('Joao permissao')), 1)
            self.assertEqual(memory.search('como foi'), [])
            memory.backup(backup)
            restored = Memory(backup)
            self.assertEqual(restored.search('João'), memory.search('João'))
            restored.db.close()
            memory.db.close()

    def test_ollama_request_contract_without_network(self):
        def respond(request, timeout):
            self.assertEqual(request.full_url, 'http://127.0.0.1:11434/api/chat')
            payload = json.loads(request.data)
            self.assertFalse(payload['stream'])
            self.assertFalse(payload['think'])
            self.assertEqual(payload['model'], 'qwen3:1.7b')
            self.assertIn('Ana', payload['messages'][0]['content'])
            return io.BytesIO(json.dumps({'message': {'content': 'Ajustando a permissão (#1).'}}).encode())
        with patch('kiki.infrastructure.ollama.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect = respond
            self.assertIn('#1', ask_ollama('Como resolveu?', [(1, 'Ana: permissão', '2026-11-12')]))

    def test_persistence_search_and_reminder_lifecycle(self):
        with database_file() as path:
            memory = Memory(path)
            memory.save('Ana: acesso corrigido com permissão.')
            memory.save('Bruno: impressora configurada.')
            memory.add_task('Conferir Ana', dt.datetime.now() - dt.timedelta(minutes=1))
            memory.add_task('Conferir Bruno', dt.datetime.now() + dt.timedelta(days=1))
            memory.db.close()
            memory = Memory(path)
            self.assertEqual(len(memory.search('Ana')), 1)
            self.assertIn('permissão', memory.search('Ana')[0][1])
            self.assertEqual(memory.search('inexistente'), [])
            overdue = memory.overdue()
            self.assertEqual(len(overdue), 1)
            memory.acknowledge([overdue[0][0]])
            self.assertEqual(memory.overdue(), [])
            self.assertEqual(len(memory.tasks()), 2)
            memory.finish(overdue[0][0])
            self.assertEqual(len(memory.tasks()), 1)
            memory.db.close()


if __name__ == '__main__':
    unittest.main()
