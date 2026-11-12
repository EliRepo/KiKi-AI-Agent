"""Desktop integration checks; skipped when no display is available."""
import tkinter as tk
import unittest
from unittest.mock import patch

from kiki.infrastructure.memory import Memory
from kiki.ui.desktop import App
from kiki.ui import appearance
from kiki.infrastructure.settings import Settings
from kiki.ui.rounded import RoundedButton


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk()
        except tk.TclError as error:
            self.skipTest(str(error))
        self.root.withdraw()
        self.memory = Memory(':memory:')
        self.app = App(self.root, self.memory)

    def tearDown(self):
        if hasattr(self, 'memory'):
            self.root.update_idletasks()
            self.root.destroy()
            self.memory.db.close()

    def test_navigation_preserves_unsaved_work(self):
        self.assertEqual(self.app.workspace.current, 'chat')
        self.app.question.insert(0, 'Pergunta em rascunho')
        self.app.workspace.select('notes')
        self.app.note.insert('1.0', 'Registro ainda não salvo')
        self.app.workspace.select('tasks')
        self.app.task.insert(0, 'Conferir Ana')
        self.app.workspace.select('config')
        self.app.model.delete(0, 'end')
        self.app.model.insert(0, 'qwen3:0.6b')
        self.app.workspace.select('chat')
        self.root.update_idletasks()
        self.assertEqual(self.app.question.get(), 'Pergunta em rascunho')
        self.assertEqual(self.app.note.get('1.0', 'end').strip(), 'Registro ainda não salvo')
        self.assertEqual(self.app.task.get(), 'Conferir Ana')
        self.assertEqual(self.app.model.get(), 'qwen3:0.6b')
        self.assertEqual(self.memory.search(''), [])

    def test_memory_and_reminder_actions_still_work(self):
        self.app.workspace.select('notes')
        self.app.note.insert('1.0', 'Ana: permissão corrigida')
        self.app.save()
        self.assertEqual(len(self.memory.search('Ana')), 1)
        self.app.workspace.select('tasks')
        self.app.task.insert(0, 'Conferir Ana')
        self.app.add_task()
        self.assertEqual(len(self.memory.tasks()), 1)
        self.app.workspace.select('chat')
        self.assertEqual(self.app.workspace.title.get(), 'Conversa')

    def test_palette_switch_preserves_drafts_and_updates_colors(self):
        self.app.note.insert('1.0', 'Não perder este rascunho')
        self.app.question.insert(0, 'Pergunta não enviada')
        with patch.object(Settings, 'save'):
            for label, theme in [('Claro', 'light'), ('Escuro', 'dark'), ('Claro', 'light')]:
                self.app.theme_choice.set(label)
                self.app.font_size_choice.set('15')
                self.app.save_settings()
                self.root.update_idletasks()
                self.assertEqual(self.app.settings.theme, theme)
                self.assertEqual(self.app.answer.cget('background'), appearance.PALETTES[theme]['BG'])
                self.assertEqual(self.app.question.cget('background'), appearance.PALETTES[theme]['SURFACE'])
                self.assertEqual(self.app.workspace.buttons['chat'].cget('background'), appearance.PALETTES[theme]['SIDEBAR'])
                self.assertEqual(self.app.note.get('1.0', 'end').strip(), 'Não perder este rascunho')
                self.assertEqual(self.app.question.get(), 'Pergunta não enviada')

    def test_rounded_button_respects_disabled_state(self):
        calls = []
        button = RoundedButton(self.root, 'Teste', lambda: calls.append(True))
        button.pack()
        self.root.update_idletasks()
        button.invoke()
        button.configure(state='disabled')
        button.invoke()
        self.assertEqual(calls, [True])
        button.configure(state='normal')
        button.invoke()
        self.assertEqual(calls, [True, True])
