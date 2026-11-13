"""Show the exact bounded evidence captured for a particular response."""
import tkinter as tk
from tkinter import ttk
from kiki.ui import appearance as a


class SourceViewer(tk.Toplevel):
    def __init__(self, parent, records, font_size=13):
        super().__init__(parent, background=a.BG)
        self.title('Registros enviados nesta consulta • KiKi')
        self.geometry('720x460')
        self.minsize(480, 300)
        self.transient(parent)
        self.bind('<Escape>', lambda event: self.destroy())
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Registros enviados à IA', font=(a.FONT, 14, 'bold')).pack(anchor='w')
        ttk.Label(body, text='Trechos de até 500 caracteres por registro. Confira se sustentam a resposta.',
                  wraplength=620, foreground=a.MUTED).pack(anchor='w', pady=(4, 12))
        area = ttk.Frame(body)
        area.pack(fill='both', expand=True)
        self.text = tk.Text(area, wrap='word', font=(a.FONT, font_size), bg=a.SURFACE,
                            fg=a.TEXT, relief='flat', padx=10, pady=10)
        scroll = ttk.Scrollbar(area, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.text.pack(side='left', fill='both', expand=True)
        self.text.insert('1.0', '\n\n'.join(f'[{identifier}] • Criado: {created}\n{text}'
                                          for identifier, text, created in records))
        self.text.configure(state='disabled')
