"""Edit or postpone an existing reminder without overwriting stale changes."""
import datetime as dt
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from kiki.domain.reminders import ReminderNotFoundError
from kiki.ui import appearance as a
from kiki.ui.rounded import RoundedButton, entry


class TaskEditor(tk.Toplevel):
    def __init__(self, parent, memory, task, on_saved, postpone_only=False, font_size=13):
        super().__init__(parent, background=a.BG)
        self.memory, self.task, self.on_saved = memory, task, on_saved
        self.postpone_only = postpone_only
        self.original_due = task.due.strftime('%d/%m/%Y %H:%M')
        self.title(('Adiar' if postpone_only else 'Editar') + f' lembrete #{task.id} • KiKi')
        self.geometry('680x420')
        self.minsize(500, 340)
        self.transient(parent)
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.bind('<Escape>', lambda event: self.cancel())
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=f'Lembrete #{task.id}', font=(a.FONT, 14, 'bold')).pack(anchor='w')
        ttk.Label(body, text='Nova data e hora: DD/MM/AAAA HH:MM (horário local)').pack(anchor='w', pady=(12, 4))
        panel, self.due = entry(body)
        self.due.insert(0, self.original_due)
        panel.pack(fill='x')
        ttk.Label(body, text='A nova data precisa estar no futuro. Adiar mantém a descrição.',
                  foreground=a.MUTED, wraplength=600).pack(anchor='w', pady=(6, 12))
        buttons = ttk.Frame(body)
        buttons.pack(side='bottom', fill='x', pady=(12, 0))
        RoundedButton(buttons, 'Salvar alterações', self.save, style='Accent.TButton', width=180).pack(side='left')
        RoundedButton(buttons, 'Cancelar', self.cancel).pack(side='left', padx=8)
        self.text = tk.Text(body, wrap='word', font=(a.FONT, font_size), bg=a.SURFACE,
                            fg=a.TEXT, insertbackground=a.TEXT, relief='flat', padx=10, pady=10, height=3)
        self.text.insert('1.0', task.text)
        if postpone_only:
            self.text.configure(state='disabled')
        self.text.pack(fill='both', expand=True)

    def save(self):
        try:
            due = dt.datetime.strptime(self.due.get().strip(), '%d/%m/%Y %H:%M')
        except ValueError:
            messagebox.showerror('Confira a data', 'Use uma data válida no formato DD/MM/AAAA HH:MM.', parent=self)
            return
        try:
            if self.postpone_only:
                self.memory.postpone_task(self.task.id, due, expected_revision=self.task.revision)
            else:
                self.memory.update_task(self.task.id, self.text.get('1.0', 'end'), due,
                                        expected_revision=self.task.revision)
        except (ValueError, ReminderNotFoundError, sqlite3.Error) as error:
            messagebox.showerror('Lembrete não alterado', str(error), parent=self)
            return
        self.destroy()
        self.on_saved()

    def cancel(self):
        changed = self.due.get() != self.original_due or self.text.get('1.0', 'end-1c') != self.task.text
        if changed and not messagebox.askyesno('Descartar alterações?', 'Descartar as alterações ainda não salvas?', parent=self):
            return
        self.destroy()
