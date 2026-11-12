import os
from pathlib import Path
import tkinter as tk
from kiki.infrastructure.memory import Memory
from kiki.ui.desktop import App
from kiki.infrastructure.settings import Settings, data_directory
from tkinter import messagebox
from kiki.infrastructure.fonts import load_bundled_fonts

def main():
    load_bundled_fonts()
    folder = data_directory()
    folder.mkdir(parents=True, exist_ok=True)
    memory = Memory(folder / 'kiki.sqlite3')
    root = tk.Tk()
    try:
        settings = Settings.load(folder)
    except ValueError as error:
        messagebox.showwarning('Configuração da KiKi', str(error) + '\nO modelo padrão será usado nesta sessão.', parent=root)
        settings = Settings()
    App(root, memory, settings, folder)
    root.mainloop()
    memory.db.close()


if __name__ == '__main__':
    main()
