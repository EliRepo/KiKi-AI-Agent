"""Open the real interface with fictional in-memory records and temporary settings."""
import argparse
import datetime as dt
import tempfile
from pathlib import Path
import tkinter as tk

from kiki.infrastructure.memory import Memory
from kiki.infrastructure.settings import Settings
from kiki.ui.desktop import App


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--agent-demo', action='store_true', help='Open a fictional combined request for review, without executing it.')
    modes.add_argument('--reminder-demo', action='store_true', help='Show a fictional reminder for editing or postponing.')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='kiki-demo-') as folder:
        memory = Memory(':memory:')
        try:
            memory.save('Ana: acesso corrigido ajustando a permissão. Registro fictício para demonstração.')
            memory.save('Mariana: cadastro revisado. Registro fictício para demonstração.')
            if args.reminder_demo:
                memory.add_task('Conferir Ana — lembrete fictício para avaliação M08',
                                (dt.datetime.now() + dt.timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0))
            root = tk.Tk()
            app = App(root, memory, Settings(), Path(folder))
            root.title('KiKi • demonstração com dados fictícios')
            app.workspace.select('notes')
            app.record_list.selection_set('1')
            app.preview_note()
            app.status.set('Demonstração com dados fictícios. Banco em memória; configurações temporárias.')
            if args.agent_demo:
                app.workspace.select('chat')
                app.question.insert(0, 'Atendi Ana, corrigi a permissão e quero conferir amanhã às dez')
                root.after(200, app.ask)
            if args.reminder_demo:
                root.title('KiKi • demonstração M08 com dados fictícios')
                app.workspace.select('tasks')
                app.task_list.selection_set('1')
            root.mainloop()
        finally:
            memory.db.close()


if __name__ == '__main__':
    main()
