"""Acceptance for bounded requests and confirmed tools; no model or network needed."""
from dataclasses import FrozenInstanceError, replace
import datetime as dt
from pathlib import Path
import tempfile
import unittest

from kiki.application.agent import AgentCoordinator
from kiki.application.tools import execute_confirmed
from kiki.domain.actions import SaveNote, CreateReminder, Clarification, ProposalState, validate_actions
from kiki.domain.requests import interpret_request
from kiki.domain.reminders import parse_reminder
from kiki.infrastructure.memory import Memory
from kiki.infrastructure.migrations import SCHEMA_VERSION

NOW = dt.datetime(2026, 11, 13, 9)
COMBINED = 'Atendi Ana, corrigi a permissão e quero conferir amanhã às dez'


class RequestTests(unittest.TestCase):
    def test_combined_roadmap_request_has_two_typed_actions(self):
        actions = interpret_request(COMBINED, NOW)
        self.assertEqual(actions[0], SaveNote('Atendi Ana, corrigi a permissão'))
        self.assertIsInstance(actions[1], CreateReminder)
        self.assertEqual(actions[1].due, dt.datetime(2026, 11, 14, 10))
        self.assertIn('Atendi Ana', actions[1].text)

    def test_explicit_commands_and_ordinary_chat_stay_separate(self):
        self.assertEqual(interpret_request('Guarde: Ana: permissão revisada.', NOW),
                         (SaveNote('Ana: permissão revisada.'),))
        actions = interpret_request('Guarde: Ana atendida; lembre-me de conferir Ana amanhã às 10h', NOW)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[1].due, dt.datetime(2026, 11, 14, 10))
        for text in ('Como resolvi o problema da Ana?', 'sim', 'Não guarde nada.',
                     'O modelo respondeu: Guarde: algo', 'Atendi Ana hoje.'):
            with self.subTest(text=text):
                self.assertIsNone(interpret_request(text, NOW))

    def test_missing_or_ambiguous_fields_never_produce_actions(self):
        for text in ('Guarde:', 'Lembre-me de conferir Ana amanhã',
                     'Lembre-me de conferir Ana às 10h', 'Lembrete: amanhã às 10h',
                     'Lembrete: dia 14/11/2026 às 10h',
                     'Lembre-me de conferir Ana amanhã às 10h ou às 11h',
                     'Lembre-me de conferir Ana 31/02/2027 às 10h',
                     'Guarde: Ana atendida; lembre-me de conferir amanhã', 'Exclua registro 1'):
            with self.subTest(text=text):
                self.assertIsInstance(interpret_request(text, NOW), Clarification)

    def test_explicit_time_vocabulary_and_unsupported_suffixes(self):
        self.assertEqual(parse_reminder('amanhã às dez e meia', NOW), dt.datetime(2026, 11, 14, 10, 30))
        self.assertEqual(parse_reminder('amanhã às vinte e três', NOW), dt.datetime(2026, 11, 14, 23))
        for phrase in ('amanhã às 10:999', 'amanhã às dez e trinta', 'amanhã às 10 da noite',
                       'hoje às 8h', 'amanhã às 10h3', 'amanhã às 10.30',
                       'amanhã às 10h 15', 'amanhã às dez e um quarto'):
            with self.subTest(phrase=phrase), self.assertRaises(ValueError):
                parse_reminder(phrase, NOW)

    def test_unknown_tool_types_and_invalid_dates_are_rejected(self):
        for actions in ((object(),), (SaveNote('a'), SaveNote('b')), ()):
            with self.assertRaises(ValueError):
                validate_actions(actions)
        with self.assertRaises(ValueError):
            CreateReminder('Algo', NOW.replace(tzinfo=dt.timezone.utc))
        with self.assertRaises(ValueError):
            CreateReminder('Algo', NOW.replace(second=10))


class CoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.memory = Memory(':memory:')
        self.addCleanup(self.memory.db.close)
        self.agent = AgentCoordinator(self.memory, clock=lambda: NOW)

    def test_confirmed_combined_request_executes_once_with_verifiable_ids(self):
        proposal = self.agent.prepare(COMBINED)
        self.assertEqual(self.memory.search(''), [])
        self.assertEqual(self.memory.tasks(), [])
        self.assertIs(proposal.state, ProposalState.PROPOSED)
        with self.assertRaises(FrozenInstanceError):
            proposal.request = 'changed'
        result = self.agent.confirm(proposal.id)
        self.assertIs(result.state, ProposalState.EXECUTED)
        self.assertEqual(self.memory.get_note(result.result.note_id).text, proposal.actions[0].text)
        self.assertEqual(self.memory.tasks()[0][0], result.result.task_id)
        repeated = self.agent.confirm(proposal.id)
        self.assertTrue(repeated.result.replayed)
        self.assertEqual(len(self.memory.search('')), 1)
        self.assertEqual(len(self.memory.tasks()), 1)
        self.assertEqual(self.memory.db.execute('SELECT COUNT(*) FROM action_receipts').fetchone()[0], 1)

    def test_cancel_and_unknown_confirmation_do_not_change_storage(self):
        proposal = self.agent.prepare(COMBINED)
        self.assertIs(self.agent.cancel(proposal.id).state, ProposalState.CANCELLED)
        for identifier in (proposal.id, 'unknown'):
            with self.assertRaises(ValueError):
                self.agent.confirm(identifier)
        self.assertEqual(self.memory.search(''), [])
        self.assertEqual(self.memory.tasks(), [])

    def test_proposed_actions_cannot_enter_the_tool(self):
        proposal = self.agent.prepare('Guarde: registro fictício')
        with self.assertRaisesRegex(ValueError, 'confirmada'):
            execute_confirmed(self.memory, proposal, NOW)
        self.assertEqual(self.memory.search(''), [])

    def test_second_action_failure_rolls_back_first_and_receipt(self):
        self.memory.db.execute("CREATE TRIGGER reject_task BEFORE INSERT ON tasks BEGIN SELECT RAISE(ABORT,'simulated failure'); END")
        proposal = self.agent.prepare(COMBINED)
        result = self.agent.confirm(proposal.id)
        self.assertIs(result.state, ProposalState.FAILED)
        self.assertIsNone(result.result)
        self.assertEqual(self.memory.search(''), [])
        self.assertEqual(self.memory.tasks(), [])
        self.assertEqual(self.memory.db.execute('SELECT COUNT(*) FROM action_receipts').fetchone()[0], 0)
        with self.assertRaises(ValueError):
            self.agent.confirm(proposal.id)

    def test_expired_reminder_blocks_the_entire_combined_request(self):
        proposal = self.agent.prepare(COMBINED)
        self.agent.clock = lambda: NOW + dt.timedelta(days=2)
        result = self.agent.confirm(proposal.id)
        self.assertIs(result.state, ProposalState.FAILED)
        self.assertIn('já passou', result.error)
        self.assertEqual(self.memory.search(''), [])
        self.assertEqual(self.memory.tasks(), [])

    def test_receipt_rejects_id_reuse_with_changed_payload(self):
        proposal = self.agent.prepare('Guarde: primeiro texto')
        self.agent.confirm(proposal.id)
        changed = replace(proposal, actions=(SaveNote('Outro texto'),), state=ProposalState.CONFIRMED)
        with self.assertRaisesRegex(ValueError, 'outro conteúdo'):
            execute_confirmed(self.memory, changed, NOW)
        self.assertEqual(len(self.memory.search('')), 1)

    def test_receipt_survives_reopening_database(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder) / 'memory.sqlite3'
            first = Memory(path)
            try:
                agent = AgentCoordinator(first, clock=lambda: NOW)
                proposal = agent.prepare(COMBINED)
                agent.confirm(proposal.id)
            finally:
                first.db.close()
            reopened = Memory(path)
            try:
                confirmed = replace(proposal, state=ProposalState.CONFIRMED)
                receipt = execute_confirmed(reopened, confirmed, NOW)
                self.assertTrue(receipt.replayed)
                self.assertEqual(len(reopened.search('')), 1)
                self.assertEqual(len(reopened.tasks()), 1)
            finally:
                reopened.db.close()

    def test_version_two_upgrade_preserves_notes_and_tasks(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as folder:
            path = Path(folder) / 'memory.sqlite3'
            old = Memory(path)
            old.save('Preservar dado fictício')
            old.add_task('Preservar lembrete', NOW + dt.timedelta(days=1))
            old.db.execute('DROP TABLE action_receipts')
            old.db.execute('PRAGMA user_version=2')
            old.db.commit()
            old.db.close()
            upgraded = Memory(path)
            try:
                self.assertTrue(upgraded.migration_backup.is_file())
                self.assertEqual(upgraded.db.execute('PRAGMA user_version').fetchone()[0], SCHEMA_VERSION)
                self.assertEqual(upgraded.search('Preservar')[0][1], 'Preservar dado fictício')
                self.assertEqual(len(upgraded.tasks()), 1)
            finally:
                upgraded.db.close()
