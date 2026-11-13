"""An explicit note editor; opening a record never changes stored data."""
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox

from kiki.domain.notes import NoteNotFoundError
from kiki.ui import appearance as a
from kiki.ui.rounded import RoundedButton


class NoteEditor(tk.Toplevel):
    def __init__(self, parent, memory, note, on_saved, font_size=13):
        super().__init__(parent, background=a.BG)
        self.memory, self.note, self.on_saved = memory, note, on_saved
        self.title(f'Editar registro #{note.id} • KiKi')
        self.geometry('680x420')
        self.minsize(480, 300)
        self.transient(parent)
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.bind('<Escape>', lambda event: self.cancel())
        self.bind('<Control-Return>', lambda event: self.save())
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text=f'Registro #{note.id}', font=(a.FONT, 14, 'bold')).pack(anchor='w')
        ttk.Label(body, text=f'Criado: {note.created}' + (f' • Alterado: {note.updated}' if note.updated else ''),
                  foreground=a.MUTED).pack(anchor='w', pady=(4, 12))
        buttons = ttk.Frame(body)
        buttons.pack(side='bottom', fill='x', pady=(12, 0))
        RoundedButton(buttons, 'Salvar alterações', self.save, style='Accent.TButton', width=180).pack(side='left')
        RoundedButton(buttons, 'Cancelar', self.cancel).pack(side='left', padx=8)
        self.text = tk.Text(body, wrap='word', font=(a.FONT, font_size), bg=a.SURFACE,
                            fg=a.TEXT, insertbackground=a.TEXT, relief='flat', padx=10, pady=10)
        self.text.insert('1.0', note.text)
        self.text.pack(fill='both', expand=True)
        self.text.focus_set()

    def save(self):
        try:
            self.memory.update_note(self.note.id, self.text.get('1.0', 'end'),
                                    expected_revision=self.note.revision)
        except (ValueError, NoteNotFoundError, sqlite3.Error) as error:
            messagebox.showerror('Registro não alterado', str(error), parent=self)
            return
        self.destroy()
        self.on_saved()

    def cancel(self):
        if self.text.get('1.0', 'end-1c') != self.note.text:
            if not messagebox.askyesno('Descartar alterações?',
                                     'As alterações deste registro ainda não foram salvas. Descartar?', parent=self):
                return
        self.destroy()
