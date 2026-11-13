import datetime as dt
import queue
import threading
import sqlite3
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from kiki.domain.reminders import parse_reminder
from kiki.infrastructure.ollama import ask_ollama
from kiki.application.context import retrieve_context
from kiki.application.diagnostics import diagnose
from kiki.infrastructure.settings import Settings, data_directory
from kiki.ui.workspace import Workspace
from kiki.ui import appearance as a
from kiki.ui.rounded import RoundedButton, RoundedPanel, entry, chooser

class App:
    def __init__(self, root, memory, settings=None, folder=None):
        self.root, self.memory = root, memory
        self.settings = settings or Settings()
        self.folder = folder or data_directory()
        self.diagnostic_messages = queue.Queue()
        self.messages = queue.Queue()
        root.title('KiKi • assistente local')
        root.geometry('1180x780')
        root.minsize(960, 680)
        a.configure_appearance(root, self.settings.theme, self.settings.font_family)
        main = ttk.Frame(root)
        main.pack(fill='both', expand=True)
        self.workspace = Workspace(main)
        chat = self.workspace.add('chat', 'Conversa', 'Converse com a KiKi usando o modelo local configurado.')
        notes = self.workspace.add('notes', 'Memória', 'Guarde informações e encontre registros salvos neste computador.')
        tasks = self.workspace.add('tasks', 'Lembretes', 'Organize suas pendências. Os avisos precisam da KiKi aberta e do computador acordado.')
        ttk.Label(notes, text='Escreva um registro para guardar ou palavras para buscar:').pack(anchor='w')
        note_panel = RoundedPanel(notes)
        note_panel.pack(fill='x', pady=8)
        self.note = tk.Text(note_panel.body, width=1, height=5, wrap='word', font=(a.FONT, 11), bg=a.SURFACE)
        self.note.pack(fill='x', pady=8)
        buttons = ttk.Frame(notes)
        buttons.pack(fill='x')
        RoundedButton(buttons, text='Guardar registro', command=self.save).pack(side='left')
        RoundedButton(buttons, text='Buscar', command=self.search).pack(side='left', padx=8)
        RoundedButton(buttons, text='Recentes', command=lambda: self.show_records('')).pack(side='left')
        self.records = tk.Text(notes, width=1, wrap='word', state='disabled', font=(a.FONT, 11))
        self.records.pack(fill='both', expand=True, pady=12)
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
        self.task_list.pack(fill='both', expand=True, pady=12)
        RoundedButton(tasks, text='Concluir selecionado', command=self.finish).pack(anchor='w')
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
        self.question = tk.Entry(input_row, font=(a.FONT, 12), bg=a.SURFACE, fg=a.TEXT,
                                  insertbackground=a.TEXT, relief='flat', highlightthickness=0)
        self.question.pack(side='left', fill='x', expand=True, ipady=10)
        self.send = RoundedButton(input_row, text='↑', command=self.ask, style='Accent.TButton', width=40, circle=True)
        self.send.pack(side='right', padx=(12, 0))
        self.question.bind('<Return>', lambda event: self.ask())
        ttk.Label(chat, text='A IA recebe até 8 registros encontrados pela busca. Confira as respostas.',
                  wraplength=600, foreground=a.MUTED, font=(a.FONT, 9)).pack(side='bottom', anchor='w')
        transcript.pack(fill='both', expand=True)
        config = self.workspace.add('config', 'Configuração', 'Escolha o modelo e verifique o ambiente. Nenhum download é iniciado automaticamente.', bottom=True)
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
        ttk.Label(config, text='Modelo local do Ollama:').pack(anchor='w')
        model_panel, self.model = entry(config)
        self.model.insert(0, self.settings.model)
        model_panel.pack(fill='x', pady=8)
        RoundedButton(config, text='Salvar e aplicar', command=self.save_settings, style='Accent.TButton').pack(anchor='w')
        self.check = RoundedButton(config, text='Verificar ambiente', command=self.run_diagnostics)
        self.check.pack(anchor='w', pady=8)
        RoundedButton(config, text='Salvar cópia de segurança…', command=self.backup).pack(anchor='w', pady=(0, 8))
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
        self.memory.save(text)
        self.note.delete('1.0', 'end')
        self.show_records('')
        self.status.set('Registro salvo neste computador.')

    def search(self):
        self.show_records(self.note.get('1.0', 'end').strip())

    def save_settings(self):
        try:
            settings = Settings(self.model.get().strip(),
                                theme='light' if self.theme_choice.get() == 'Claro' else 'dark',
                                font_family=self.font_choice.get(), font_size=int(self.font_size_choice.get()))
            settings.save(self.folder)
        except (ValueError, OSError) as error:
            messagebox.showerror('Configuração não salva', str(error))
            return
        old_palette = a.PALETTES[self.settings.theme]
        self.settings = settings
        a.configure_appearance(self.root, settings.theme, settings.font_family)
        a.update_widgets(self.root, old_palette)
        self.workspace.select(self.workspace.current)
        self.apply_reading_size()
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

    def show_records(self, query):
        rows = self.memory.search(query)
        self.display(self.records, '\n\n'.join(f'#{i} • {created}\n{text}' for i, text, created in rows) or 'Nenhum registro encontrado.')

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
        selected = self.task_list.selection()
        if selected:
            self.memory.finish(int(selected[0]))
            self.refresh_tasks()

    def tick(self):
        rows = self.memory.overdue()
        if rows:
            self.root.bell()
            messagebox.showinfo('KiKi • lembretes pendentes', '\n\n'.join(f'{text}\n{dt.datetime.fromisoformat(due):%d/%m/%Y %H:%M}' for _, text, due in rows))
            self.memory.acknowledge([i for i, _, _ in rows])
        self.root.after(15000, self.tick)

    def ask(self):
        if str(self.send.cget('state')) == 'disabled':
            return
        question = self.question.get().strip()
        if not question:
            return
        records = retrieve_context(self.memory, question)
        self.send.configure(state='disabled')
        self.status.set('Consultando o Ollama local…')
        settings = self.settings
        def worker():
            try:
                answer = ask_ollama(question, records, settings)
            except Exception:
                answer = 'Não consegui consultar o Ollama local. Abra Configuração no menu à esquerda e clique em Verificar ambiente.\n\nSua memória e seus lembretes continuam disponíveis.'
            self.messages.put((question, answer))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            self.display(self.diagnostic_result, self.diagnostic_messages.get_nowait())
            self.check.configure(state='normal')
        except queue.Empty:
            pass
        try:
            question, answer = self.messages.get_nowait()
            self.display(self.answer, f'Você: {question}\n\nKiKi: {answer}')
            self.send.configure(state='normal')
            self.status.set('Pronta. A conversa não foi salva como registro.')
        except queue.Empty:
            pass
        self.root.after(200, self.poll)


