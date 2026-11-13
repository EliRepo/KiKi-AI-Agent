import unittest
from kiki.application.context import retrieve_context, unverified_citations
from kiki.infrastructure.memory import Memory


class ContextTests(unittest.TestCase):
    def test_search_acceptance_with_whole_words_accents_and_missing_facts(self):
        memory = Memory(':memory:')
        try:
            memory.save('Ana: acesso corrigido com permissão.')
            memory.save('Mariana: cadastro revisado.')
            memory.save('Bruno: impressora configurada.')
            memory.save('João: permissão revisada.')
            memory.save('Fiz uma revisão do relatório.')
            cases = [
                ('Como resolvi o problema da Ana?', [1]),
                ('Mariana', [2]),
                ('Joao permissao', [4, 1]),
                ('Bruno impressora', [3]),
                ('telefone Carla', []),
                ('como foi', []),
                ('impressora', [3]),
                ('acesso Ana', [1]),
                ('PERMISSÃO', [4, 1]),
                ('O que fiz para Bruno?', [3]),
                ('Ana?', [1]),
                ('relatorio', [5]),
            ]
            for question, expected in cases:
                with self.subTest(question=question):
                    self.assertEqual([row[0] for row in retrieve_context(memory, question)], expected)
        finally:
            memory.db.close()

    def test_citations_are_checked_against_sent_ids_only(self):
        records = [(7, 'Registro fictício', '2026-11-13')]
        self.assertEqual(unverified_citations('Conforme [7] e #7.', records), [])
        self.assertEqual(unverified_citations('Conforme [8], [8] e #12.', records), [8, 12])
        self.assertEqual(unverified_citations('2 + 2 = 4. [1]', []), [1])
        self.assertEqual(unverified_citations('Sem citações.', records), [])

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
