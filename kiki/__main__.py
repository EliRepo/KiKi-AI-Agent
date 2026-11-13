import sqlite3
import argparse
import tkinter as tk
from kiki.infrastructure.memory import Memory
from kiki.ui.desktop import App
from kiki.infrastructure.settings import Settings, data_directory
from tkinter import messagebox
from kiki.infrastructure.fonts import load_bundled_fonts

def main():
    parser = argparse.ArgumentParser(description='KiKi — assistente pessoal local')
    parser.add_argument('--smoke-test', metavar='RESULTADO_JSON', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.smoke_test:
        from kiki.smoke import run_smoke
        return run_smoke(args.smoke_test)
    load_bundled_fonts()
    folder = data_directory()
    root = tk.Tk()
    root.withdraw()
    try:
        folder.mkdir(parents=True, exist_ok=True)
        memory = Memory(folder / 'kiki.sqlite3')
    except (OSError, sqlite3.Error, ValueError) as error:
        messagebox.showerror('Não foi possível abrir a memória', str(error), parent=root)
        root.destroy()
        return 1
    try:
        settings = Settings.load(folder)
    except ValueError as error:
        messagebox.showwarning('Configuração da KiKi', str(error) + '\nO modelo padrão será usado nesta sessão.', parent=root)
        settings = Settings()
    try:
        app = App(root, memory, settings, folder)
        if memory.migration_backup:
            app.status.set(f'Memória atualizada. Cópia anterior preservada em {memory.migration_backup}')
        root.deiconify()
        root.mainloop()
    finally:
        memory.db.close()


if __name__ == '__main__':
    raise SystemExit(main())
