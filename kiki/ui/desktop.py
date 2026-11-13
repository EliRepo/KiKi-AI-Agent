import datetime as dt
import queue
import threading
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from kiki.domain.reminders import parse_reminder, ReminderNotFoundError
from kiki.infrastructure.ollama import ask_ollama, OllamaError
from kiki.application.context import retrieve_context, unverified_citations
from kiki.application.diagnostics import diagnose
from kiki.infrastructure.settings import Settings, data_directory
from kiki.ui.workspace import Workspace
from kiki.ui import appearance as a
from kiki.ui.rounded import RoundedButton, RoundedPanel, entry, chooser
from kiki.ui.note_editor import NoteEditor
from kiki.domain.notes import NoteNotFoundError
from kiki.ui.sources import SourceViewer
from kiki.infrastructure.recovery import restore_backup_copy
from kiki.application.agent import AgentCoordinator
from kiki.domain.actions import ActionProposal, Clarification, ProposalState, CreateReminder
from kiki.ui.proposal import ProposalDialog
from kiki.ui.task_editor import TaskEditor
from kiki.application.chat import ChatManager
from kiki.ui.chat_input import ChatInput

class App:
    def __init__(self, root, memory, settings=None, folder=None):
        self.root, self.memory = root, memory
        self.settings = settings or Settings()
        self.folder = folder or data_directory()
        self.diagnostic_messages = queue.Queue()
        self.messages = queue.Queue()
        self.record_query = ''
        self.note_editor = None
        self.context_sources = ()
        self.agent = AgentCoordinator(memory)
        self.proposal_dialog = None
        self.task_editor = None
        self.chat = ChatManager(memory, self.settings.history_enabled, self.settings.history_days)
        self.pending_chat = None
        root.title('KiKi • assistente local')
        root.geometry('1180x780')
        root.minsize(960, 680)
        a.configure_appearance(root, self.settings.theme, self.settings.font_family)
        main = ttk.Frame(root)
        main.pack(fill='both', expand=True)
        self.workspace = Workspace(main)
        history = self.workspace.history_area
        RoundedButton(history, text='Nova conversa', command=self.new_chat, width=190).pack(fill='x')
        self.history_status = tk.StringVar()
        ttk.Label(history, textvariable=self.history_status, wraplength=195, foreground=a.MUTED).pack(anchor='w', pady=5)
        self.chat_list = ttk.Treeview(history, show='tree', selectmode='browse', height=4)
        self.chat_list.column('#0', width=180)
        self.chat_list.pack(fill='both', expand=True)
        self.chat_list.bind('<Double-1>', self.open_chat)
        self.chat_list.bind('<Return>', self.open_chat)
        RoundedButton(history, text='Abrir selecionada', command=self.open_chat, width=190).pack(fill='x', pady=(4, 0))
        RoundedButton(history, text='Excluir conversa…', command=self.delete_chat, width=190).pack(fill='x', pady=(4, 0))
        chat = self.workspace.add('chat', 'Conversa', 'Converse com a KiKi usando o modelo local configurado.')
        notes = self.workspace.add('notes', 'Memória', 'Guarde informações e encontre registros salvos neste computador.')
        tasks = self.workspace.add('tasks', 'Lembretes', 'Organize suas pendências. Os avisos precisam da KiKi aberta e do computador acordado.')
        ttk.Label(notes, text='Escreva um registro para guardar ou palavras para buscar:').pack(anchor='w')
        note_panel = RoundedPanel(notes)
        note_panel.pack(fill='x', pady=8)
        self.note = tk.Text(note_panel.body, width=1, height=3, wrap='word', font=(a.FONT, 11), bg=a.SURFACE)
        self.note.pack(fill='x', pady=8)
        buttons = ttk.Frame(notes)
        buttons.pack(fill='x')
        RoundedButton(buttons, text='Guardar registro', command=self.save).pack(side='left')
        RoundedButton(buttons, text='Buscar', command=self.search).pack(side='left', padx=8)
        RoundedButton(buttons, text='Recentes', command=lambda: self.show_records('')).pack(side='left')
        record_actions = ttk.Frame(notes)
        record_actions.pack(fill='x', pady=(8, 0))
        RoundedButton(record_actions, text='Editar selecionado', command=self.edit_note, width=175).pack(side='left')
        RoundedButton(record_actions, text='Excluir selecionado…', command=self.delete_note, width=195).pack(side='left', padx=8)
        self.record_list = ttk.Treeview(notes, columns=('id', 'text'), show='headings', selectmode='browse', height=4)
        self.record_list.heading('id', text='Registro')
        self.record_list.heading('text', text='Texto (selecione para ler abaixo)')
        self.record_list.column('id', width=75, stretch=False)
        self.record_list.column('text', width=300)
        self.record_list.pack(fill='x', pady=(10, 4))
        self.record_list.bind('<<TreeviewSelect>>', lambda event: self.preview_note())
        self.record_list.bind('<Double-1>', lambda event: self.edit_note())
        self.record_list.bind('<Return>', lambda event: self.edit_note())
        self.records = tk.Text(notes, width=1, height=3, wrap='word', state='disabled', font=(a.FONT, 11))
        self.records.pack(fill='both', expand=True, pady=(4, 8))
        ttk.Label(tasks, text='O que você precisa fazer?').pack(anchor='w')
        task_panel, self.task = entry(tasks)
        task_panel.pack(fill='x', pady=8)
        ttk.Label(tasks, text='Data e hora: DD/MM/AAAA HH:MM (horário deste computador)').pack(anchor='w')
        due_panel, self.due = entry(tasks)
        self.due.insert(0, (dt.datetime.now() + dt.timedelta(hours=1)).strftime('%d/%m/%Y %H:%M'))
        due_panel.pack(fill='x', pady=8)
        ttk.Label(tasks, text='Ou escreva: “conferir Ana amanhã às 10h” e confira a data preenchida.').pack(anchor='w')
        phrase_panel, self.phrase = entry(tasks)
        phrase_panel.pack(fill='x', pady=4)
        RoundedButton(tasks, text='Preencher pela frase', command=self.prepare_reminder).pack(anchor='w', pady=4)
        RoundedButton(tasks, text='Criar lembrete', command=self.add_task).pack(anchor='w')
        self.task_list = ttk.Treeview(tasks, columns=('due', 'text'), show='headings', selectmode='browse')
        self.task_list.heading('due', text='Quando')
        self.task_list.heading('text', text='Lembrete')
        self.task_list.column('due', width=150, stretch=False)
        task_actions = ttk.Frame(tasks)
        task_actions.pack(side='bottom', fill='x', pady=(8, 0))
        RoundedButton(task_actions, text='Concluir', command=self.finish, width=110).grid(row=0, column=0, padx=(0, 8), pady=4)
        RoundedButton(task_actions, text='Editar…', command=self.edit_task, width=110).grid(row=0, column=1, padx=(0, 8), pady=4)
        RoundedButton(task_actions, text='Adiar…', command=lambda: self.edit_task(postpone_only=True), width=110).grid(row=0, column=2, padx=(0, 8), pady=4)
        RoundedButton(task_actions, text='Cancelar lembrete…', command=self.cancel_task, width=200).grid(row=1, column=0, columnspan=2, sticky='w', pady=4)
        self.task_list.configure(height=3)
        self.task_list.pack(fill='both', expand=True, pady=(10, 0))
        transcript = ttk.Frame(chat)
        self.answer = tk.Text(transcript, width=1, wrap='word', state='disabled', font=(a.FONT, 12),
                              bg=a.BG, fg=a.TEXT, relief='flat', padx=18, pady=32, spacing1=3, spacing3=5)
        scroll = ttk.Scrollbar(transcript, command=self.answer.yview)
        self.answer.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.answer.pack(side='left', fill='both', expand=True)
        self.display(self.answer, 'Como posso ajudar?\n\nConverse com sua memória. Organize seu dia.\nTudo começa por aqui.\n\nUse Memória para guardar informações e Lembretes\npara acompanhar suas pendências.')
        self.answer.tag_configure('welcome_title', font=(a.FONT, 25, 'bold'), foreground=a.TEXT, spacing3=15)
        self.answer.tag_add('welcome_title', '1.0', '1.end')
        self.answer.tag_configure('welcome_body', foreground=a.MUTED, font=(a.FONT, 12))
        self.answer.tag_add('welcome_body', '2.0', 'end')
        composer = RoundedPanel(chat, padding=14, radius=28)
        composer.pack(side='bottom', fill='x', pady=(16, 12))
        input_row = tk.Frame(composer.body, bg=a.SURFACE)
        input_row.pack(fill='x')
        self.question = ChatInput(input_row, height=2, width=1, wrap='word', font=(a.FONT, 12), bg=a.SURFACE, fg=a.TEXT,
                                  insertbackground=a.TEXT, relief='flat', highlightthickness=0)
        self.question.pack(side='left', fill='x', expand=True, ipady=10)
        self.send = RoundedButton(input_row, text='↑', command=self.ask, style='Accent.TButton', width=40, circle=True)
        self.send.pack(side='right', padx=(12, 0))
        self.question.bind('<Return>', self.send_enter)
        self.question.bind('<Shift-Return>', self.question.newline)
        ttk.Label(chat, text='Enter envia • Shift+Enter: nova linha. A IA recebe até 8 registros e até 6 mensagens anteriores.',
                  wraplength=600, foreground=a.MUTED, font=(a.FONT, 9)).pack(side='bottom', anchor='w')
        source_actions = ttk.Frame(chat)
        source_actions.pack(side='bottom', fill='x', pady=(8, 4))
        self.source_button = RoundedButton(source_actions, text='Fontes da consulta', command=self.show_sources, width=310)
        self.source_button.configure(state='disabled')
        self.source_button.pack(side='left')
        RoundedButton(source_actions, text='Copiar resposta', command=self.copy_response, width=165).pack(side='left', padx=(8, 0))
        ttk.Label(chat, text='Pedidos: “Guarde: texto” ou “Lembre-me de conferir Ana amanhã às 10h”. Sempre há conferência.',
                  wraplength=600, foreground=a.MUTED, font=(a.FONT, 9)).pack(side='bottom', anchor='w', pady=(4, 0))
        transcript.pack(fill='both', expand=True)
        placeholder = self.workspace.add('config', 'Configuração', '', bottom=True)
        del self.workspace.pages['config']
        placeholder.destroy()
        self.settings_window = tk.Toplevel(root)
        self.settings_window.withdraw()
        self.settings_window.title('KiKi • Configuração')
        self.settings_window.configure(bg=a.BG)
        self.settings_window.geometry('760x660')
        self.settings_window.minsize(700, 600)
        self.settings_window.protocol('WM_DELETE_WINDOW', self.settings_window.withdraw)
        self.workspace.commands['config'] = self.open_settings
        self.settings_save = RoundedButton(self.settings_window, text='Salvar e aplicar', command=self.save_settings, style='Accent.TButton')
        self.settings_save.pack(side='bottom', anchor='w', padx=30, pady=(0, 14))
        tabs = ttk.Notebook(self.settings_window)
        tabs.pack(fill='both', expand=True, padx=14, pady=14)
        appearance = ttk.Frame(tabs, padding=16)
        model = ttk.Frame(tabs, padding=16)
        data = ttk.Frame(tabs, padding=16)
        about = ttk.Frame(tabs, padding=16)
        for page, title in ((appearance, 'Aparência'), (model, 'Modelo'), (data, 'Dados'), (about, 'Sobre')):
            tabs.add(page, text=title)
        config = appearance
        ttk.Label(config, text='Aparência e leitura', font=(a.FONT, 13, 'bold')).pack(anchor='w', pady=(0, 8))
        appearance_row = ttk.Frame(config)
        appearance_row.pack(fill='x', pady=(0, 10))
        theme_box = ttk.Frame(appearance_row)
        theme_box.pack(side='left', padx=(0, 14))
        ttk.Label(theme_box, text='Tema').pack(anchor='w')
        self.theme_choice = tk.StringVar(value='Claro' if self.settings.theme == 'light' else 'Escuro')
        chooser(theme_box, self.theme_choice, ['Claro', 'Escuro'], width=12).pack(fill='x')
        font_box = ttk.Frame(appearance_row)
        font_box.pack(side='left', padx=(0, 14))
        ttk.Label(font_box, text='Fonte de leitura').pack(anchor='w')
        self.font_choice = tk.StringVar(value=self.settings.font_family)
        chooser(font_box, self.font_choice, a.available_fonts(root), width=19).pack(fill='x')
        size_box = ttk.Frame(appearance_row)
        size_box.pack(side='left')
        ttk.Label(size_box, text='Tamanho').pack(anchor='w')
        self.font_size_choice = tk.StringVar(value=str(self.settings.font_size))
        chooser(size_box, self.font_size_choice, [str(i) for i in range(11, 19)], width=3).pack(fill='x')
        self.font_status = tk.StringVar(value=f'Fonte em uso: {a.FONT}. A opção automática usa uma fonte instalada no computador.')
        ttk.Label(config, textvariable=self.font_status, foreground=a.MUTED, wraplength=600).pack(anchor='w', pady=(0, 14))
        config = model
        ttk.Label(config, text='Modelo local do Ollama:').pack(anchor='w')
        model_panel, self.model = entry(config)
        self.model.insert(0, self.settings.model)
        model_panel.pack(fill='x', pady=8)
        self.check = RoundedButton(config, text='Verificar ambiente', command=self.run_diagnostics)
        self.check.pack(anchor='w', pady=8)
        self.history_choice = tk.BooleanVar(value=self.settings.history_enabled)
        self.retention_choice = tk.StringVar(value=str(self.settings.history_days))
        ttk.Checkbutton(data, text='Salvar conversas localmente (inclui respostas e fontes)', variable=self.history_choice).pack(anchor='w')
        ttk.Label(data, text='Retenção em dias: 7, 30, 90; 0 = até excluir manualmente.').pack(anchor='w', pady=(16, 4))
        chooser(data, self.retention_choice, ['7', '30', '90', '0'], width=8).pack(anchor='w')
        ttk.Label(data, text='Desativado por padrão. Ativar não salva conversas anteriores.\nDesativar mantém o histórico existente e inicia outra conversa ao enviar.\nA retenção é aplicada ao abrir o aplicativo ou salvar esta configuração.\nExcluir histórico não apaga notas, lembretes ou cópias de segurança.',
                  wraplength=620).pack(anchor='w', pady=16)
        RoundedButton(data, text='Apagar todo o histórico…', command=self.clear_history, width=280).pack(anchor='w', pady=8)
        RoundedButton(data, text='Salvar cópia de segurança…', command=self.backup).pack(anchor='w', pady=(0, 8))
        RoundedButton(data, text='Restaurar cópia em novo arquivo…', command=self.restore_copy, width=335).pack(anchor='w', pady=(0, 8))
        ttk.Label(about, text='KiKi • assistente local\n\nProtótipo em avaliação. Conversas, notas e lembretes têm controles separados.\nRespostas do modelo não executam ferramentas. Pedidos explícitos exigem confirmação.\n\nAvisos exigem o aplicativo aberto e computador acordado.\nOllama e modelo são instalados separadamente. Nenhum download é iniciado aqui.', wraplength=620).pack(anchor='w')
        self.diagnostic_result = tk.Text(config, width=1, wrap='word', state='disabled', font=(a.FONT, 11))
        self.diagnostic_result.pack(fill='both', expand=True)
        self.display(self.diagnostic_result, f'Dados: {self.folder}\n\nClique em Verificar ambiente. A verificação não envia registros para a IA.')
        self.status = tk.StringVar(value='Pronta. Registros e lembretes funcionam sem Ollama.')
        ttk.Label(main, textvariable=self.status, wraplength=1100, padding=(16, 7),
                  foreground=a.MUTED, font=(a.FONT, 9)).pack(side='bottom', fill='x')
        self.workspace.pack(fill='both', expand=True)
        self.workspace.select('chat')
        self.show_records('')
        self.refresh_tasks()
        self.refresh_chats()
        self.apply_reading_size()
        root.after(1000, self.tick)
        root.after(200, self.poll)

    @staticmethod
    def display(widget, content):
        widget.configure(state='normal')
        widget.delete('1.0', 'end')
        widget.insert('end', content)
        widget.configure(state='disabled')

    def save(self):
        text = self.note.get('1.0', 'end').strip()
        if not text:
            return
        try:
            self.memory.save(text)
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror('Registro não salvo', str(error), parent=self.root)
            return
        self.note.delete('1.0', 'end')
        self.show_records('')
        self.status.set('Registro salvo neste computador.')

    def search(self):
        self.show_records(self.note.get('1.0', 'end').strip())

    def save_settings(self):
        try:
            settings = Settings(self.model.get().strip(),
                                theme='light' if self.theme_choice.get() == 'Claro' else 'dark',
                                font_family=self.font_choice.get(), font_size=int(self.font_size_choice.get()),
                                history_enabled=self.history_choice.get(), history_days=int(self.retention_choice.get()))
            self.chat._idle()
            settings.save(self.folder)
            self.chat.configure(settings.history_enabled, settings.history_days)
        except (ValueError, OSError, sqlite3.Error) as error:
            messagebox.showerror('Configuração não salva', str(error))
            return
        old_palette = a.PALETTES[self.settings.theme]
        self.settings = settings
        a.configure_appearance(self.root, settings.theme, settings.font_family)
        a.update_widgets(self.root, old_palette)
        self.workspace.select(self.workspace.current)
        self.apply_reading_size()
        self.refresh_chats()
        self.render_chat()
        self.font_status.set(f'Fonte em uso: {a.FONT}. Preferência: {settings.font_family}.')
        self.status.set('Configuração salva. Aparência aplicada e preservada para a próxima abertura.')

    def apply_reading_size(self):
        for widget in (self.answer, self.note, self.records, self.diagnostic_result, self.question):
            widget.configure(font=(a.FONT, self.settings.font_size))
        self.answer.configure(spacing1=4, spacing3=8)
        self.answer.tag_configure('welcome_body', font=(a.FONT, self.settings.font_size))
        for widget in (self.note, self.records, self.diagnostic_result):
            widget.configure(spacing1=2, spacing3=5)

    def run_diagnostics(self):
        settings = self.settings
        self.check.configure(state='disabled')
        self.display(self.diagnostic_result, 'Verificando o serviço local…')
        def worker():
            try:
                result = diagnose(settings, self.folder)
            except Exception:
                result = 'Não foi possível concluir o diagnóstico. Verifique sua instalação do Ollama.'
            self.diagnostic_messages.put(result)
        threading.Thread(target=worker, daemon=True).start()

    def backup(self):
        path = filedialog.asksaveasfilename(title='Salvar cópia da memória e dos lembretes', defaultextension='.sqlite3', initialfile=f'KiKi-{dt.datetime.now():%Y-%m-%d-%H%M%S}.sqlite3', filetypes=[('Banco SQLite', '*.sqlite3')])
        if path:
            current = self.memory.db.execute('PRAGMA database_list').fetchone()[2]
            if current and Path(path).resolve() == Path(current).resolve():
                messagebox.showerror('Escolha outro arquivo', 'A cópia precisa ter um nome diferente do banco em uso.')
                return
            try:
                self.memory.backup(path)
                self.status.set('Cópia salva. Ela contém seus dados: guarde em um local protegido.')
            except (OSError, sqlite3.Error) as error:
                messagebox.showerror('Não foi possível salvar a cópia', str(error))

    def prepare_reminder(self):
        phrase = self.phrase.get().strip()
        try:
            due = parse_reminder(phrase)
        except ValueError as error:
            messagebox.showerror('Confira a frase', str(error))
            return
        self.task.delete(0, 'end')
        self.task.insert(0, phrase)
        self.due.delete(0, 'end')
        self.due.insert(0, due.strftime('%d/%m/%Y %H:%M'))
        self.status.set('Confira a descrição e a data. Clique em Criar lembrete para salvar.')

    def restore_copy(self):
        source = filedialog.askopenfilename(title='Escolha a cópia de segurança da KiKi',
                                            filetypes=[('Banco SQLite', '*.sqlite3')])
        if not source:
            return
        destination = filedialog.asksaveasfilename(title='Restaurar em arquivo novo — o banco atual será preservado',
                                                  initialfile='KiKi-restaurada.sqlite3', defaultextension='.sqlite3',
                                                  filetypes=[('Banco SQLite', '*.sqlite3')])
        if not destination:
            return
        try:
            restored = restore_backup_copy(source, destination)
        except (ValueError, OSError, sqlite3.Error) as error:
            messagebox.showerror('Cópia não restaurada', str(error), parent=self.root)
            return
        self.status.set(f'Cópia verificada e restaurada em {restored}. O banco atual não foi substituído.')

    def show_records(self, query):
        self.record_query = query
        rows = self.memory.search(query)
        self.record_list.delete(*self.record_list.get_children())
        for identifier, text, _ in rows:
            self.record_list.insert('', 'end', iid=str(identifier), values=(f'#{identifier}', text.replace('\n', ' ')[:160]))
        self.display(self.records, 'Selecione um registro para ler, editar ou excluir.' if rows else 'Nenhum registro encontrado.')

    def selected_note(self):
        selected = self.record_list.selection()
        if not selected:
            self.status.set('Selecione um registro na lista.')
            return None
        try:
            return self.memory.get_note(int(selected[0]))
        except NoteNotFoundError as error:
            self.status.set(str(error))
            self.show_records(self.record_query)
            return None

    def preview_note(self):
        if not self.record_list.selection():
            return
        note = self.selected_note()
        if note is not None:
            dates = f'Criado: {note.created}' + (f' • Alterado: {note.updated}' if note.updated else '')
            self.display(self.records, f'#{note.id} • {dates}\n\n{note.text}')

    def edit_note(self):
        if self.note_editor is not None and self.note_editor.winfo_exists():
            self.note_editor.lift()
            self.note_editor.text.focus_set()
            return
        note = self.selected_note()
        if note is not None:
            self.note_editor = NoteEditor(self.root, self.memory, note, self.note_saved,
                                          font_size=self.settings.font_size)

    def note_saved(self):
        self.show_records(self.record_query)
        self.status.set('Alterações salvas neste computador.')

    def delete_note(self):
        note = self.selected_note()
        if note is None:
            return
        if not messagebox.askyesno('Excluir registro?',
                                  f'Excluir o registro #{note.id}?\n\n{note.text[:250]}\n\n'
                                  'A exclusão não tem desfazer. Cópias de segurança existentes não são alteradas.',
                                  parent=self.root):
            return
        try:
            self.memory.delete_note(note.id, expected_revision=note.revision)
        except (ValueError, NoteNotFoundError, sqlite3.Error) as error:
            messagebox.showerror('Registro não excluído', str(error), parent=self.root)
            return
        self.show_records(self.record_query)
        self.status.set(f'Registro #{note.id} excluído da memória atual.')

    def add_task(self):
        text = self.task.get().strip()
        try:
            due = dt.datetime.strptime(self.due.get().strip(), '%d/%m/%Y %H:%M')
            if not text or due <= dt.datetime.now():
                raise ValueError()
        except ValueError:
            messagebox.showerror('Confira o lembrete', 'Informe uma descrição e uma data futura no formato DD/MM/AAAA HH:MM.')
            return
        self.memory.add_task(text, due)
        self.task.delete(0, 'end')
        self.refresh_tasks()
        self.status.set('Lembrete salvo. Mantenha a KiKi aberta e o computador acordado.')

    def refresh_tasks(self):
        self.task_list.delete(*self.task_list.get_children())
        for i, text, due in self.memory.tasks():
            self.task_list.insert('', 'end', iid=str(i), values=(dt.datetime.fromisoformat(due).strftime('%d/%m/%Y %H:%M'), text))

    def finish(self):
        task = self.selected_task()
        if task is None:
            return
        try:
            self.memory.finish(task.id, expected_revision=task.revision)
        except (ValueError, ReminderNotFoundError, sqlite3.Error) as error:
            messagebox.showerror('Lembrete não concluído', str(error), parent=self.root)
            return
        self.refresh_tasks()
        self.status.set(f'Lembrete #{task.id} concluído.')

    def selected_task(self):
        selected = self.task_list.selection()
        if not selected:
            self.status.set('Selecione um lembrete na lista.')
            return None
        try:
            return self.memory.get_task(int(selected[0]))
        except ReminderNotFoundError as error:
            self.status.set(str(error))
            self.refresh_tasks()
            return None

    def edit_task(self, postpone_only=False):
        if self.task_editor is not None and self.task_editor.winfo_exists():
            self.task_editor.lift()
            return
        task = self.selected_task()
        if task is not None:
            self.task_editor = TaskEditor(self.root, self.memory, task, self.task_saved,
                                          postpone_only=postpone_only, font_size=self.settings.font_size)

    def task_saved(self):
        self.refresh_tasks()
        self.status.set('Lembrete atualizado. O aviso será apresentado na nova data com a KiKi aberta.')

    def cancel_task(self):
        task = self.selected_task()
        if task is None:
            return
        if not messagebox.askyesno('Cancelar lembrete?',
                                  f'Cancelar o lembrete #{task.id}?\n\n{task.text}\n{task.due:%d/%m/%Y %H:%M}\n\n'
                                  'Ele sairá das pendências e não gerará novos avisos.', parent=self.root):
            return
        try:
            self.memory.cancel_task(task.id, expected_revision=task.revision)
        except (ValueError, ReminderNotFoundError, sqlite3.Error) as error:
            messagebox.showerror('Lembrete não cancelado', str(error), parent=self.root)
            return
        self.refresh_tasks()
        self.status.set(f'Lembrete #{task.id} cancelado.')

    def tick(self):
        rows = self.memory.overdue()
        if rows:
            self.root.bell()
            messagebox.showinfo('KiKi • lembretes pendentes', '\n\n'.join(f'{text}\n{dt.datetime.fromisoformat(due):%d/%m/%Y %H:%M}' for _, text, due in rows))
            self.memory.acknowledge([i for i, _, _ in rows])
        self.root.after(15000, self.tick)

    def open_settings(self):
        if self.settings_window.state() == 'withdrawn':
            x = max(0, self.root.winfo_rootx() + 60)
            y = max(0, self.root.winfo_rooty() + 35)
            self.settings_window.geometry(f'+{x}+{y}')
        self.settings_window.deiconify()
        self.settings_window.lift()

    def copy_response(self):
        message = next((message for message in reversed(self.chat.current.messages)
                        if message.role == 'assistant' and message.status != 'pending'), None)
        if message is None:
            self.status.set('Nenhuma resposta para copiar nesta conversa.')
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(message.text)
        self.status.set('Última resposta copiada.')

    def send_enter(self, event=None):
        self.ask()
        return 'break'

    def refresh_chats(self):
        self.chat_list.delete(*self.chat_list.get_children())
        for key, title, stored in self.chat.summaries():
            self.chat_list.insert('', 'end', iid=key, text=('● ' if stored else '○ ') + title)
        self.chat_list.selection_set(self.chat.current_key)
        self.chat_list.see(self.chat.current_key)
        self.history_status.set('Histórico salvo neste PC' if self.chat.history_enabled else 'Histórico desativado • só nesta sessão')

    def render_chat(self):
        lines = []
        self.context_sources = ()
        for message in self.chat.current.messages:
            author = 'Você' if message.role == 'user' else 'Falha na consulta' if message.status == 'error' else 'KiKi'
            lines.append(f'{author}: {message.text}')
            if message.role == 'assistant':
                self.context_sources = message.sources
        self.display(self.answer, '\n\n'.join(lines) if lines else 'Como posso ajudar?\n\nEnter envia. Shift+Enter insere uma nova linha.\nUse Nova conversa para começar sem o contexto anterior.')
        self.answer.see('end')
        self.source_button.text = f'Ver {len(self.context_sources)} registro(s) enviado(s) à IA' if self.context_sources else 'Consulta sem registros de memória'
        self.source_button.configure(state='normal' if self.context_sources else 'disabled')

    def new_chat(self):
        try:
            self.chat.current.draft = self.question.get()
            self.chat.new_chat()
        except ValueError as error:
            self.status.set(str(error))
            return
        self.question.delete(0, 'end')
        self.refresh_chats()
        self.render_chat()
        self.workspace.select('chat')
        self.question.focus_set()

    def open_chat(self, event=None):
        selected = self.chat_list.selection()
        if not selected:
            return
        try:
            self.chat.current.draft = self.question.get()
            self.chat.open_chat(selected[0])
        except (ValueError, sqlite3.Error) as error:
            self.status.set(str(error))
            return
        self.question.delete(0, 'end')
        self.question.insert(0, self.chat.current.draft)
        self.refresh_chats()
        self.render_chat()
        self.workspace.select('chat')

    def delete_chat(self):
        selected = self.chat_list.selection()
        if not selected:
            return
        try:
            self.chat._idle()
            if not messagebox.askyesno('Excluir conversa?', 'Excluir esta conversa? Não há desfazer. Notas, lembretes e backups serão preservados.', parent=self.root):
                return
            self.chat.delete_chat(selected[0])
        except (ValueError, sqlite3.Error) as error:
            self.status.set(str(error))
            return
        self.question.delete(0, 'end')
        self.refresh_chats()
        self.render_chat()

    def clear_history(self):
        try:
            self.chat._idle()
            if not messagebox.askyesno('Apagar histórico?', 'Apagar todas as conversas, inclusive desta sessão? Não há desfazer. Notas, lembretes e backups serão preservados.', parent=self.settings_window):
                return
            self.chat.clear_history()
        except (ValueError, sqlite3.Error) as error:
            self.status.set(str(error))
            return
        self.question.delete(0, 'end')
        self.refresh_chats()
        self.render_chat()

    def complete_chat(self, binding, text, status='ok', sources=()):
        try:
            self.chat.complete(*binding, text, status, sources)
        except sqlite3.Error as error:
            messagebox.showerror('Resposta não salva no histórico', 'A resposta está visível nesta sessão, mas não foi salva. ' + str(error), parent=self.root)
        self.render_chat()
        self.refresh_chats()

    def ask(self):
        if str(self.send.cget('state')) == 'disabled':
            return
        question = self.question.get().strip()
        if not question:
            return
        prepared = self.agent.prepare(question)
        try:
            records = retrieve_context(self.memory, question) if prepared is None else ()
        except sqlite3.Error as error:
            messagebox.showerror('Consulta não iniciada', str(error), parent=self.root)
            return
        # These turns precede this question. New chats never inherit another chat's context.
        history = self.chat.context()
        if (not self.chat.history_enabled and self.chat.current.stored_id is not None) or (
            self.chat.history_enabled and self.chat.current.stored_id is None and self.chat.current.messages
        ):
            history = []
        try:
            binding = self.chat.begin(question, 'action' if prepared is not None else 'ok')
        except (ValueError, sqlite3.Error) as error:
            messagebox.showerror('Consulta não iniciada', str(error), parent=self.root)
            return
        self.pending_chat = binding
        self.render_chat()
        self.refresh_chats()
        if prepared is not None:
            self.context_sources = ()
            self.source_button.configure(state='disabled')
            if isinstance(prepared, Clarification):
                self.complete_chat(binding, prepared.message, 'action')
                self.status.set('Confira os dados do pedido. Nenhuma ação foi executada.')
            elif isinstance(prepared, ActionProposal):
                self.send.configure(state='disabled')
                self.status.set('Aguardando conferência. Nenhuma ação foi executada.')
                self.proposal_dialog = ProposalDialog(self.root, self.agent, prepared, self.action_done,
                                                      font_size=self.settings.font_size)
            return
        self.send.configure(state='disabled')
        self.status.set('Consultando o Ollama local…')
        settings = self.settings
        def worker():
            succeeded = False
            try:
                answer = ask_ollama(question, records, settings, history=history)
                succeeded = True
            except OllamaError as error:
                answer = str(error) + '\n\nSua memória e seus lembretes continuam disponíveis.'
            except Exception:
                answer = 'Não consegui consultar o Ollama local. Abra Configuração no menu à esquerda e clique em Verificar ambiente.\n\nSua memória e seus lembretes continuam disponíveis.'
            self.messages.put((binding, question, answer, succeeded, tuple(records)))
        threading.Thread(target=worker, daemon=True).start()

    def action_done(self, proposal):
        self.send.configure(state='normal')
        if proposal.state is ProposalState.CANCELLED:
            text = 'Pedido cancelado. Nenhuma ação foi executada.'
        elif proposal.state is ProposalState.FAILED:
            text = 'Não foi possível executar o pedido. ' + (proposal.error or '') + '\nConfira a memória e os lembretes antes de refazer o pedido.'
        elif proposal.result.replayed:
            text = 'Esse pedido já foi executado. Nenhuma gravação foi repetida.'
        else:
            lines = []
            if proposal.result.note_id is not None:
                lines.append(f'Registro #{proposal.result.note_id} salvo na memória.')
            if proposal.result.task_id is not None:
                reminder = next(action for action in proposal.actions if type(action) is CreateReminder)
                lines.append(f'Lembrete #{proposal.result.task_id} criado para {reminder.due:%d/%m/%Y %H:%M}.')
            text = '\n'.join(lines)
            self.show_records(self.record_query)
            self.refresh_tasks()
        self.complete_chat(self.pending_chat, text, 'action')
        self.status.set(text.split('\n')[0])

    def show_sources(self):
        if self.context_sources:
            return SourceViewer(self.root, self.context_sources, font_size=self.settings.font_size)

    def poll(self):
        try:
            self.display(self.diagnostic_result, self.diagnostic_messages.get_nowait())
            self.check.configure(state='normal')
        except queue.Empty:
            pass
        try:
            binding, question, answer, succeeded, sources = self.messages.get_nowait()
            self.context_sources = sources
            self.source_button.text = f'Ver {len(sources)} registro(s) enviado(s) à IA' if sources else 'Consulta sem registros de memória'
            self.source_button.configure(state='normal' if sources else 'disabled')
            missing = unverified_citations(answer, sources) if succeeded else []
            if missing:
                answer += '\n\nAtenção: a resposta citou IDs não enviados nesta consulta: ' + ', '.join(f'[{i}]' for i in missing) + '. Confira as fontes.'
            self.complete_chat(binding, answer, 'ok' if succeeded else 'error', sources)
            if succeeded and self.question.get().strip() == question:
                self.question.delete(0, 'end')
            self.send.configure(state='normal')
            self.status.set('Pronta. A conversa não foi salva como registro.' if succeeded else
                            'Falha na consulta. Confira a mensagem e tente novamente. Memória e lembretes disponíveis.')
            if missing:
                self.status.set('Resposta com citações não verificadas. Confira o aviso e as fontes da consulta.')
        except queue.Empty:
            pass
        self.root.after(200, self.poll)


