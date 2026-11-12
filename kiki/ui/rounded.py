"""Rounded native Tk controls, with keyboard focus and theme refresh."""
import tkinter as tk
from . import appearance as a


def shape(canvas, width, height, radius, fill, outline=''):
    r = min(radius, height / 2, width / 2)
    points = [r, 1, width-r, 1, width-1, 1, width-1, r,
              width-1, height-r, width-1, height-1, width-r, height-1,
              r, height-1, 1, height-1, 1, height-r, 1, r, 1, 1]
    return canvas.create_polygon(points, smooth=True, splinesteps=30,
                                 fill=fill, outline=outline or fill)


class RoundedPanel(tk.Canvas):
    def __init__(self, parent, padding=12, radius=18):
        super().__init__(parent, bg=a.BG, highlightthickness=0, bd=0, height=50)
        self.padding, self.radius = padding, radius
        self.body = tk.Frame(self, bg=a.SURFACE)
        self.window = self.create_window(padding, padding, anchor='nw', window=self.body)
        self.bind('<Configure>', self.layout)
        self.body.bind('<Configure>', self.fit_height)

    def fit_height(self, event=None):
        required = self.body.winfo_reqheight() + self.padding * 2
        if self.winfo_reqheight() != required:
            self.configure(height=required)

    def layout(self, event=None):
        self.itemconfigure(self.window, width=max(1, self.winfo_width() - self.padding * 2))
        self.refresh_theme()

    def refresh_theme(self):
        self.configure(bg=a.BG)
        self.body.configure(bg=a.SURFACE)
        self.delete('surface')
        item = shape(self, max(2, self.winfo_width()), max(2, self.winfo_height()), self.radius, a.SURFACE, a.BORDER)
        self.addtag_withtag('surface', item)
        self.tag_lower('surface')


class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, style=None, width=None, circle=False):
        self.text, self.command = text, command
        self.accent = style == 'Accent.TButton'
        self.circle, self.hover = circle, False
        super().__init__(parent, width=width or max(90, len(text) * 8 + 30), height=40,
                         bg=a.BG, highlightthickness=0, takefocus=True, cursor='hand2', bd=0)
        for event in ('<Configure>', '<FocusIn>', '<FocusOut>'):
            self.bind(event, self.refresh_theme)
        self.bind('<Enter>', lambda e: self.set_hover(True))
        self.bind('<Leave>', lambda e: self.set_hover(False))
        self.bind('<Button-1>', lambda e: self.invoke())
        self.bind('<Return>', lambda e: self.invoke())
        self.bind('<space>', lambda e: self.invoke())

    def configure(self, cnf=None, **kwargs):
        result = super().configure(cnf, **kwargs)
        if hasattr(self, 'accent') and kwargs:
            self.refresh_theme()
        return result

    config = configure

    def set_hover(self, value):
        self.hover = value
        self.refresh_theme()

    def invoke(self):
        if str(self.cget('state')) != 'disabled':
            self.command()

    def refresh_theme(self, event=None):
        self.delete('all')
        disabled = str(self.cget('state')) == 'disabled'
        color = a.SURFACE if disabled else a.BUTTON if self.accent else a.HOVER if self.hover else a.SURFACE
        foreground = a.MUTED if disabled else a.ON_BUTTON if self.accent else a.TEXT
        # Parent may itself be a rounded surface.
        parent_bg = self.master.cget('background') if 'background' in self.master.keys() else a.BG
        super().configure(bg=parent_bg)
        w, h = max(2, self.winfo_width()), max(2, self.winfo_height())
        shape(self, w, h, h/2 if self.circle else 12, color,
              a.FOCUS if self.focus_get() == self else color)
        self.create_text(w/2, h/2, text=self.text, fill=foreground,
                         font=(a.FONT, 17 if self.circle else 11))


def entry(parent, **kwargs):
    panel = RoundedPanel(parent, padding=10, radius=14)
    field = tk.Entry(panel.body, bg=a.SURFACE, fg=a.TEXT, insertbackground=a.TEXT,
                     relief='flat', highlightthickness=0, font=(a.FONT, 11), **kwargs)
    field.pack(fill='x', expand=True)
    return panel, field


def chooser(parent, variable, values, width):
    """A pill menu; the operating-system popup remains native."""
    panel = RoundedPanel(parent, padding=3, radius=12)
    menu = tk.OptionMenu(panel.body, variable, *values)
    menu.configure(bg=a.SURFACE, fg=a.TEXT, activebackground=a.HOVER, activeforeground=a.TEXT,
                   relief='flat', bd=0, highlightthickness=0, width=width, font=(a.FONT, 10), anchor='w')
    menu['menu'].configure(bg=a.SURFACE, fg=a.TEXT, activebackground=a.SELECTED,
                           activeforeground=a.TEXT, relief='flat', bd=0, font=(a.FONT, 10))
    menu.pack(fill='x')
    return panel
