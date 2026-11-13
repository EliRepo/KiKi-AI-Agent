"""Desktop integration checks; skipped when no display is available."""
import tkinter as tk
import unittest
from unittest.mock import patch

from kiki.infrastructure.memory import Memory
from kiki.ui.desktop import App
from kiki.ui import appearance
from kiki.infrastructure.settings import Settings
from kiki.ui.rounded import RoundedButton
from kiki.infrastructure.ollama import OllamaError


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
            for callback in self.root.tk.call('after', 'info'):
                self.root.after_cancel(callback)
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

    def test_composer_stays_visible_at_minimum_window_size(self):
        self.root.deiconify()
        self.root.geometry('960x680')
        self.root.update()
        for widget in (self.app.question, self.app.send):
            self.assertTrue(widget.winfo_viewable())
            self.assertGreater(widget.winfo_height(), 10)
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                 self.root.winfo_rooty() + self.root.winfo_height())

    def test_inference_failure_is_visible_and_allows_retry(self):
        self.app.question.insert(0, 'Pergunta fictícia')
        with patch('kiki.ui.desktop.threading.Thread') as thread, \
             patch('kiki.ui.desktop.ask_ollama', side_effect=OllamaError('Modelo ausente.')):
            thread.return_value.start.side_effect = lambda: thread.call_args.kwargs['target']()
            self.app.ask()
            self.app.ask()  # A second send must remain blocked while the result is queued.
            self.assertEqual(self.app.messages.qsize(), 1)
            self.app.poll()
        self.assertIn('Falha na consulta', self.app.answer.get('1.0', 'end'))
        self.assertIn('Modelo ausente', self.app.answer.get('1.0', 'end'))
        self.assertIn('Falha na consulta', self.app.status.get())
        self.assertEqual(str(self.app.send.cget('state')), 'normal')
        self.assertEqual(self.app.question.get(), 'Pergunta fictícia')
        self.assertEqual(self.memory.search(''), [])

    def test_successful_inference_restores_ready_state(self):
        self.app.question.insert(0, 'Pergunta fictícia')
        with patch('kiki.ui.desktop.threading.Thread') as thread, \
             patch('kiki.ui.desktop.ask_ollama', return_value='Resposta fictícia.'):
            thread.return_value.start.side_effect = lambda: thread.call_args.kwargs['target']()
            self.app.ask()
            self.app.poll()
        self.assertIn('KiKi: Resposta fictícia.', self.app.answer.get('1.0', 'end'))
        self.assertTrue(self.app.status.get().startswith('Pronta.'))
        self.assertEqual(str(self.app.send.cget('state')), 'normal')
        self.assertEqual(self.memory.search(''), [])

    def test_sources_keep_the_sent_snapshot_and_flag_unknown_citations(self):
        identifier = self.memory.save('Ana: texto enviado originalmente')
        self.app.question.insert(0, 'Ana')
        with patch('kiki.ui.desktop.threading.Thread') as thread, \
             patch('kiki.ui.desktop.ask_ollama', return_value='Resposta com origem inventada [999].'):
            thread.return_value.start.side_effect = lambda: thread.call_args.kwargs['target']()
            self.app.ask()
            self.memory.update_note(identifier, 'Ana: texto corrigido depois do envio', expected_revision=1)
            self.app.poll()
        self.assertIn('IDs não enviados', self.app.answer.get('1.0', 'end'))
        self.assertIn('citações não verificadas', self.app.status.get())
        viewer = self.app.show_sources()
        snapshot = viewer.text.get('1.0', 'end')
        self.assertIn('texto enviado originalmente', snapshot)
        self.assertNotIn('corrigido depois', snapshot)
        viewer.destroy()

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

    def test_note_editor_saves_without_losing_the_new_note_draft(self):
        identifier = self.memory.save('Ana: antigo')
        self.app.show_records('Ana')
        self.app.record_list.selection_set(str(identifier))
        self.app.note.insert('1.0', 'Novo registro ainda não salvo')
        self.app.edit_note()
        editor = self.app.note_editor
        editor.text.delete('1.0', 'end')
        editor.text.insert('1.0', 'Ana: corrigido')
        editor.save()
        self.assertEqual(self.memory.get_note(identifier).text, 'Ana: corrigido')
        self.assertEqual(self.app.note.get('1.0', 'end').strip(), 'Novo registro ainda não salvo')
        self.assertEqual(self.app.record_query, 'Ana')

    def test_memory_list_and_preview_fit_minimum_window(self):
        self.root.deiconify()
        self.root.geometry('960x680')
        self.app.workspace.select('notes')
        self.root.update()
        for widget in (self.app.record_list, self.app.records):
            self.assertTrue(widget.winfo_viewable())
            self.assertGreater(widget.winfo_height(), 20)
            self.assertLessEqual(widget.winfo_rooty() + widget.winfo_height(),
                                 self.root.winfo_rooty() + self.root.winfo_height())

    def test_delete_requires_confirmation_and_keeps_changed_record(self):
        identifier = self.memory.save('Registro fictício')
        self.app.show_records('')
        self.app.record_list.selection_set(str(identifier))
        with patch('kiki.ui.desktop.messagebox.askyesno', return_value=False):
            self.app.delete_note()
        self.assertEqual(self.memory.get_note(identifier).text, 'Registro fictício')
        def change_before_confirmation(*args, **kwargs):
            self.memory.update_note(identifier, 'Registro atualizado', expected_revision=1)
            return True
        with patch('kiki.ui.desktop.messagebox.askyesno', side_effect=change_before_confirmation), \
             patch('kiki.ui.desktop.messagebox.showerror') as error:
            self.app.delete_note()
        error.assert_called_once()
        self.assertEqual(self.memory.get_note(identifier).text, 'Registro atualizado')
        with patch('kiki.ui.desktop.messagebox.askyesno', return_value=True):
            self.app.delete_note()
        self.assertEqual(self.memory.search(''), [])

    def test_cancel_editor_preserves_stored_text(self):
        identifier = self.memory.save('Original fictício')
        self.app.show_records('')
        self.app.record_list.selection_set(str(identifier))
        self.app.edit_note()
        editor = self.app.note_editor
        editor.text.insert('end', ' modificado')
        with patch('kiki.ui.note_editor.messagebox.askyesno', return_value=False):
            editor.cancel()
        self.assertTrue(editor.winfo_exists())
        with patch('kiki.ui.note_editor.messagebox.askyesno', return_value=True):
            editor.cancel()
        self.assertFalse(editor.winfo_exists())
        self.assertEqual(self.memory.get_note(identifier).text, 'Original fictício')

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
