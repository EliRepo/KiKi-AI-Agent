"""A compact chat workspace with persistent pages and two-level navigation."""
import tkinter as tk
from tkinter import ttk
from . import appearance as a


class NavItem(tk.Canvas):
    def __init__(self, parent, title, command):
        super().__init__(parent, height=36, bg=a.SIDEBAR, highlightthickness=0,
                         takefocus=True, cursor='hand2')
        self.title, self.command, self.selected = title, command, False
        self.hover = False
        self.bind('<Configure>', self.draw)
        self.bind('<Enter>', lambda e: self.set_hover(True))
        self.bind('<Leave>', lambda e: self.set_hover(False))
        self.bind('<Button-1>', lambda e: self.command())
        self.bind('<Return>', lambda e: self.command())
        self.bind('<space>', lambda e: self.command())
        self.bind('<FocusIn>', self.draw)
        self.bind('<FocusOut>', self.draw)

    def set_hover(self, value):
        self.hover = value
        self.draw()

    def set_selected(self, value):
        self.selected = value
        self.draw()

    def draw(self, event=None):
        self.delete('all')
        w, h, r = self.winfo_width(), 36, 9
        color = a.SELECTED if self.selected else a.HOVER if self.hover else a.SIDEBAR
        points = [r, 2, w-r, 2, w-2, 2, w-2, r, w-2, h-r, w-2, h-2,
                  w-r, h-2, r, h-2, 2, h-2, 2, h-r, 2, r, 2, 2]
        self.create_polygon(points, smooth=True, fill=color,
                            outline=a.FOCUS if self.focus_get() == self else color)
        self.create_text(15, 18, anchor='w', text=self.title,
                         fill=a.TEXT if self.selected else a.MUTED, font=(a.FONT, 10))


class Workspace(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pages, self.buttons, self.icons = {}, {}, {}
        self.commands = {}
        self.current = None
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self.rail = tk.Frame(self, bg=a.RAIL, width=52)
        self.rail.grid(row=0, column=0, sticky='nsew')
        self.rail.grid_propagate(False)
        self.rail.columnconfigure(0, weight=1)
        self.rail.rowconfigure(4, weight=1)
        tk.Label(self.rail, text='K', font=(a.FONT, 13, 'bold'), bg=a.RAIL, fg=a.TEXT).grid(
            row=0, column=0, pady=(22, 28))
        sidebar = tk.Frame(self, bg=a.SIDEBAR, width=230)
        sidebar.grid(row=0, column=1, sticky='nsew')
        sidebar.grid_propagate(False)
        sidebar.columnconfigure(0, weight=1)
        sidebar.rowconfigure(4, weight=1)
        tk.Label(sidebar, text='KiKi', bg=a.SIDEBAR, fg=a.TEXT, font=(a.FONT, 14, 'bold'),
                 anchor='w').grid(row=0, column=0, sticky='ew', padx=18, pady=(24, 3))
        tk.Label(sidebar, text='Seu espaço de conversa', bg=a.SIDEBAR, fg=a.MUTED,
                 font=(a.FONT, 9), anchor='w').grid(row=1, column=0, sticky='ew', padx=18, pady=(0, 30))
        tk.Label(sidebar, text='Espaço de trabalho', bg=a.SIDEBAR, fg=a.MUTED,
                 font=(a.FONT, 9, 'bold'), anchor='w').grid(row=2, column=0, sticky='ew', padx=18, pady=(0, 8))
        self.navigation = tk.Frame(sidebar, bg=a.SIDEBAR)
        self.navigation.grid(row=3, column=0, sticky='ew', padx=9)
        self.history_area = ttk.Frame(sidebar, padding=(10, 8))
        self.history_area.grid(row=4, column=0, sticky='nsew')
        self.bottom = tk.Frame(sidebar, bg=a.SIDEBAR)
        self.bottom.grid(row=5, column=0, sticky='ew', padx=9, pady=8)
        tk.Frame(sidebar, height=1, bg=a.BORDER).grid(row=6, column=0, sticky='ew', padx=18)
        tk.Label(sidebar, text='●  Armazenamento local', bg=a.SIDEBAR, fg=a.ACCENT, font=(a.FONT, 9),
                 anchor='w').grid(row=7, column=0, sticky='ew', padx=18, pady=(15, 20))
        area = ttk.Frame(self, padding=(30, 22))
        area.grid(row=0, column=2, sticky='nsew')
        area.columnconfigure(0, weight=1)
        area.rowconfigure(3, weight=1)
        self.title, self.description = tk.StringVar(), tk.StringVar()
        ttk.Label(area, textvariable=self.title, font=(a.FONT, 12, 'bold')).grid(row=0, column=0, sticky='w')
        ttk.Label(area, textvariable=self.description, foreground=a.MUTED, wraplength=580,
                  font=(a.FONT, 9)).grid(row=1, column=0, sticky='ew', pady=(5, 17))
        tk.Frame(area, height=1, bg=a.BORDER).grid(row=2, column=0, sticky='ew', pady=(0, 18))
        self.content = ttk.Frame(area)
        self.content.grid(row=3, column=0, sticky='nsew')
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

    def draw_icon(self, canvas, key, selected=False):
        canvas.delete('all')
        color = a.TEXT if selected else a.MUTED
        canvas.configure(bg=a.SELECTED if selected else a.RAIL)
        if key == 'chat':
            canvas.create_rectangle(9, 10, 25, 23, outline=color, width=1.5)
            canvas.create_line(10, 23, 10, 27, 15, 23, fill=color, width=1.5)
        elif key == 'notes':
            canvas.create_rectangle(10, 8, 24, 27, outline=color, width=1.5)
            for y in (13, 17, 21):
                canvas.create_line(14, y, 21, y, fill=color)
        elif key == 'tasks':
            canvas.create_oval(8, 8, 27, 27, outline=color, width=1.5)
            canvas.create_line(18, 12, 18, 18, 22, 20, fill=color, width=1.5)
        else:
            canvas.create_oval(9, 9, 26, 26, outline=color, width=1.5)
            canvas.create_oval(15, 15, 20, 20, outline=color, width=1.5)
            for x1, y1, x2, y2 in [(17, 5, 17, 9), (17, 26, 17, 30), (5, 17, 9, 17), (26, 17, 30, 17)]:
                canvas.create_line(x1, y1, x2, y2, fill=color, width=1.5)

    def add(self, key, title, description, bottom=False):
        page = ttk.Frame(self.content)
        page.grid(row=0, column=0, sticky='nsew')
        self.pages[key] = (page, title, description)
        item = NavItem(self.bottom if bottom else self.navigation, title, lambda: self.select(key))
        item.pack(fill='x', pady=2)
        self.buttons[key] = item
        icon = tk.Canvas(self.rail, width=35, height=35, bg=a.RAIL, highlightthickness=0, cursor='hand2')
        row = 5 if bottom else len(self.icons) + 1
        icon.grid(row=row, column=0, pady=8 if not bottom else 22)
        icon.bind('<Button-1>', lambda e: self.select(key))
        self.icons[key] = icon
        self.draw_icon(icon, key)
        return page

    def select(self, key):
        if key in self.commands:
            self.commands[key]()
            return
        page, title, description = self.pages[key]
        page.tkraise()
        self.current = key
        self.title.set(title)
        self.description.set(description)
        for name, button in self.buttons.items():
            button.set_selected(name == key)
            self.draw_icon(self.icons[name], name, name == key)
