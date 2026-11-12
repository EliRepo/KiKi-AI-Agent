import unittest
from kiki.application.context import retrieve_context
from kiki.infrastructure.memory import Memory


class ContextTests(unittest.TestCase):
    def test_context_is_bounded_and_keeps_source_identifiers(self):
        memory = Memory(':memory:')
        try:
            for _ in range(12):
                memory.save('Ana: ' + 'x' * 2000)
            records = retrieve_context(memory, 'Ana')
            self.assertEqual(len(records), 8)
            self.assertTrue(all(len(text) <= 500 for _, text, _ in records))
            self.assertEqual(records[0][0], 12)
            self.assertEqual(retrieve_context(memory, 'Bruno'), [])
        finally:
            memory.db.close()
