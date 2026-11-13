"""Read-only proposal review, explicitly bound to one coordinator ID."""
import tkinter as tk
from tkinter import ttk
from kiki.domain.actions import SaveNote, CreateReminder
from kiki.ui import appearance as a
from kiki.ui.rounded import RoundedButton


class ProposalDialog(tk.Toplevel):
    def __init__(self, parent, agent, proposal, on_done, font_size=13):
        super().__init__(parent, background=a.BG)
        self.agent, self.proposal, self.on_done = agent, proposal, on_done
        self.title('Conferir pedido antes de executar • KiKi')
        self.geometry('760x480')
        self.minsize(520, 360)
        self.transient(parent)
        self.protocol('WM_DELETE_WINDOW', self.cancel)
        self.bind('<Escape>', lambda event: self.cancel())
        body = ttk.Frame(self, padding=18)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='Confira antes de confirmar', font=(a.FONT, 15, 'bold')).pack(anchor='w')
        ttk.Label(body, text='Nada foi gravado ainda. Confirmar executa todas as ações abaixo juntas.',
                  wraplength=680, foreground=a.MUTED).pack(anchor='w', pady=(4, 8))
        ttk.Label(body, text=f'Pedido: {proposal.id}', foreground=a.MUTED).pack(anchor='w', pady=(0, 8))
        buttons = ttk.Frame(body)
        buttons.pack(side='bottom', fill='x', pady=(12, 0))
        self.confirm_button = RoundedButton(buttons, 'Confirmar e executar', self.confirm,
                                            style='Accent.TButton', width=235)
        self.confirm_button.pack(side='left')
        RoundedButton(buttons, 'Cancelar', self.cancel, width=110).pack(side='left', padx=8)
        area = ttk.Frame(body)
        area.pack(fill='both', expand=True)
        self.text = tk.Text(area, wrap='word', font=(a.FONT, font_size), bg=a.SURFACE,
                            fg=a.TEXT, relief='flat', padx=10, pady=10)
        scroll = ttk.Scrollbar(area, command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.text.pack(side='left', fill='both', expand=True)
        lines = []
        for action in proposal.actions:
            if type(action) is SaveNote:
                lines.append(f'GUARDAR REGISTRO\n{action.text}')
            elif type(action) is CreateReminder:
                lines.append(f'CRIAR LEMBRETE\nQuando: {action.due:%d/%m/%Y %H:%M} (horário deste computador)\n{action.text}')
        self.text.insert('1.0', '\n\n'.join(lines))
        self.text.configure(state='disabled')

    def confirm(self):
        if not self.winfo_exists() or str(self.confirm_button.cget('state')) == 'disabled':
            return
        self.confirm_button.configure(state='disabled')
        result = self.agent.confirm(self.proposal.id)
        self.destroy()
        self.on_done(result)

    def cancel(self):
        if not self.winfo_exists():
            return
        result = self.agent.cancel(self.proposal.id)
        self.destroy()
        self.on_done(result)
