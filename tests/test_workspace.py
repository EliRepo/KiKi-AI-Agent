"""Desktop integration checks; skipped when no display is available."""
import tkinter as tk
import datetime as dt
import unittest
from unittest.mock import patch

from kiki.infrastructure.memory import Memory
from kiki.ui.desktop import App
from kiki.ui import appearance
from kiki.infrastructure.settings import Settings
from kiki.ui.rounded import RoundedButton
from kiki.infrastructure.ollama import OllamaError
from kiki.domain.actions import ProposalState


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

    def test_action_preview_cancels_without_model_or_database_changes(self):
        self.app.question.insert(0, 'Guarde: registro fictício para cancelar')
        with patch('kiki.ui.desktop.ask_ollama') as model:
            self.app.ask()
            dialog = self.app.proposal_dialog
            self.assertEqual(str(dialog.text.cget('state')), 'disabled')
            self.assertIn('registro fictício', dialog.text.get('1.0', 'end'))
            self.assertEqual(self.memory.search(''), [])
            self.app.ask()  # A second send remains blocked during review.
            self.assertIs(self.app.proposal_dialog, dialog)
            dialog.cancel()
        model.assert_not_called()
        self.assertEqual(self.memory.search(''), [])
        self.assertIn('cancelado', self.app.answer.get('1.0', 'end'))
        self.assertEqual(str(self.app.send.cget('state')), 'normal')

    def test_confirm_button_executes_combined_request_and_refreshes_views(self):
        self.app.question.insert(0, 'Atendi Ana, corrigi a permissão e quero conferir amanhã às dez')
        with patch('kiki.ui.desktop.ask_ollama') as model:
            self.app.ask()
            dialog = self.app.proposal_dialog
            proposal_id = dialog.proposal.id
            self.assertIn('10:00', dialog.text.get('1.0', 'end'))
            self.assertEqual(self.memory.tasks(), [])
            dialog.confirm()
            dialog.confirm()  # A queued second click on a closed dialog has no effect.
        model.assert_not_called()
        self.assertEqual(len(self.memory.search('Ana')), 1)
        self.assertEqual(len(self.memory.tasks()), 1)
        self.assertEqual(len(self.app.task_list.get_children()), 1)
        self.assertEqual(len(self.app.record_list.get_children()), 1)
        self.assertIs(self.app.agent.get(proposal_id).state, ProposalState.EXECUTED)
        self.assertIn('Registro #1 salvo', self.app.answer.get('1.0', 'end'))
        self.assertIn('Lembrete #1 criado', self.app.answer.get('1.0', 'end'))

    def test_missing_action_fields_do_not_open_confirmation_or_call_model(self):
        self.app.question.insert(0, 'Lembre-me de conferir Ana amanhã')
        with patch('kiki.ui.desktop.ask_ollama') as model:
            self.app.ask()
        model.assert_not_called()
        self.assertIsNone(self.app.proposal_dialog)
        self.assertEqual(self.memory.tasks(), [])
        self.assertIn('horário', self.app.answer.get('1.0', 'end'))

    def test_action_failure_is_not_displayed_as_success(self):
        self.app.question.insert(0, 'Atendi Ana, corrigi a permissão e quero conferir amanhã às dez')
        self.app.ask()
        self.memory.db.execute("CREATE TRIGGER reject_agent_task BEFORE INSERT ON tasks BEGIN SELECT RAISE(ABORT,'falha fictícia'); END")
        self.app.proposal_dialog.confirm()
        self.assertEqual(self.memory.search(''), [])
        self.assertEqual(self.memory.tasks(), [])
        text = self.app.answer.get('1.0', 'end')
        self.assertIn('Não foi possível executar', text)
        self.assertNotIn('Registro #', text)
        self.assertEqual(str(self.app.send.cget('state')), 'normal')

    def test_reminder_edit_and_postpone_refresh_list(self):
        due = (dt.datetime.now() + dt.timedelta(days=2)).replace(second=0, microsecond=0)
        self.memory.add_task('Conferir Ana', due)
        self.app.refresh_tasks()
        self.app.task_list.selection_set('1')
        self.app.edit_task()
        self.app.task_editor.text.delete('1.0', 'end')
        self.app.task_editor.text.insert('1.0', 'Conferir Ana e Bruno')
        self.app.task_editor.save()
        self.assertEqual(self.memory.get_task(1).text, 'Conferir Ana e Bruno')
        self.app.task_list.selection_set('1')
        self.app.edit_task(postpone_only=True)
        editor = self.app.task_editor
        self.assertEqual(str(editor.text.cget('state')), 'disabled')
        editor.due.delete(0, 'end')
        editor.due.insert(0, (due + dt.timedelta(days=1)).strftime('%d/%m/%Y %H:%M'))
        editor.save()
        self.assertEqual(self.memory.get_task(1).due, due + dt.timedelta(days=1))

    def test_reminder_cancel_requires_confirmation(self):
        self.memory.add_task('Conferir fictício', dt.datetime.now() + dt.timedelta(days=1))
        self.app.refresh_tasks()
        self.app.task_list.selection_set('1')
        with patch('kiki.ui.desktop.messagebox.askyesno', return_value=False):
            self.app.cancel_task()
        self.assertFalse(self.memory.get_task(1).cancelled)
        with patch('kiki.ui.desktop.messagebox.askyesno', return_value=True):
            self.app.cancel_task()
        self.assertTrue(self.memory.get_task(1).cancelled)
        self.assertEqual(self.app.task_list.get_children(), ())

    def test_invalid_reminder_date_keeps_editor_and_original_data(self):
        due = (dt.datetime.now() + dt.timedelta(days=2)).replace(second=0, microsecond=0)
        self.memory.add_task('Preservar lembrete fictício', due)
        self.app.refresh_tasks()
        self.app.task_list.selection_set('1')
        self.app.edit_task()
        editor = self.app.task_editor
        editor.due.delete(0, 'end')
        editor.due.insert(0, '31/02/2027 10:00')
        with patch('kiki.ui.task_editor.messagebox.showerror') as error:
            editor.save()
        error.assert_called_once()
        self.assertTrue(editor.winfo_exists())
        self.assertEqual(self.memory.get_task(1).due, due)

    def test_reminder_list_stays_visible_at_minimum_window(self):
        self.root.deiconify()
        self.root.geometry('960x680')
        self.app.workspace.select('tasks')
        self.root.update()
        self.assertTrue(self.app.task_list.winfo_viewable())
        self.assertGreater(self.app.task_list.winfo_height(), 20)
        self.assertLessEqual(self.app.task_list.winfo_rooty() + self.app.task_list.winfo_height(),
                             self.root.winfo_rooty() + self.root.winfo_height())

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
