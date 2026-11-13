"""Violet palettes and in-place styling, preserving drafts and active jobs."""
import tkinter as tk
from tkinter import ttk, font as tkfont
from kiki.infrastructure.fonts import load_bundled_fonts

PALETTES = {
    'dark': dict(BG='#191622', SIDEBAR='#15111e', RAIL='#100d17', SURFACE='#262032',
                 TEXT='#f1edf8', MUTED='#b9afcb', BORDER='#493d5d', SELECTED='#3b2b55',
                 HOVER='#30253f', FOCUS='#c0a0fa', ACCENT='#b99af6', BUTTON='#6b3cb8',
                 ON_BUTTON='#ffffff', SELECTION='#55357f'),
    'light': dict(BG='#faf8ff', SIDEBAR='#f1ebfa', RAIL='#e9e0f5', SURFACE='#ffffff',
                  TEXT='#2c203d', MUTED='#6b597e', BORDER='#c9b9df', SELECTED='#e0cff7',
                  HOVER='#e9def7', FOCUS='#7845bb', ACCENT='#6936a5', BUTTON='#7240b3',
                  ON_BUTTON='#fffaff', SELECTION='#e2d2f7'),
}
globals().update(PALETTES['dark'])
FONT = 'Arial'


def available_fonts(root):
    installed = set(tkfont.families(root))
    return ['Automática'] + [name for name in (
        'Inter', 'Inter Variable', 'Segoe UI Variable Text', 'Segoe UI Variable',
        'Segoe UI', 'Arial', 'Aptos', 'DejaVu Sans') if name in installed]


def choose_font(root, requested):
    choices = available_fonts(root)[1:]
    if requested in choices:
        return requested
    # Arial precedes classic Segoe here to offer a distinct reading face on Windows 10.
    for preferred in ('Inter', 'Inter Variable', 'Segoe UI Variable Text', 'Segoe UI Variable', 'Arial', 'Segoe UI', 'DejaVu Sans'):
        if preferred in choices:
            return preferred
    return tkfont.nametofont('TkDefaultFont', root=root).actual('family')


def configure_appearance(root, theme='dark', family='Automática'):
    global FONT
    load_bundled_fonts()
    globals().update(PALETTES[theme])
    FONT = choose_font(root, family)
    root.configure(background=BG)
    for option, value in [('background', BG), ('foreground', TEXT), ('insertBackground', TEXT),
                          ('selectBackground', SELECTION), ('relief', 'flat'), ('highlightThickness', 0)]:
        root.option_add('*Text.' + option, value)
    style = ttk.Style(root)
    if style.theme_use() != 'clam':
        style.theme_use('clam')
    style.configure('.', font=(FONT, 11), background=BG, foreground=TEXT)
    style.configure('TFrame', background=BG)
    style.configure('TLabel', background=BG, foreground=TEXT)
    style.configure('Muted.TLabel', foreground=MUTED)
    style.configure('TButton', background=SURFACE, foreground=TEXT, borderwidth=0, padding=(14, 9))
    style.map('TButton', background=[('active', HOVER)], foreground=[('disabled', MUTED)])
    style.configure('Accent.TButton', background=BUTTON, foreground=ON_BUTTON)
    style.map('Accent.TButton', background=[('active', BUTTON), ('disabled', SURFACE)],
              foreground=[('disabled', MUTED), ('!disabled', ON_BUTTON)])
    for name in ('TEntry', 'TCombobox'):
        style.configure(name, fieldbackground=SURFACE, background=SURFACE, foreground=TEXT,
                        insertcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER, padding=8)
        style.map(name, bordercolor=[('focus', FOCUS)],
                  fieldbackground=[('readonly', SURFACE)], foreground=[('readonly', TEXT)])
    root.option_add('*TCombobox*Listbox.background', SURFACE)
    root.option_add('*TCombobox*Listbox.foreground', TEXT)
    root.option_add('*TCombobox*Listbox.selectBackground', SELECTED)
    root.option_add('*TCombobox*Listbox.selectForeground', TEXT)
    style.configure('Treeview', background=BG, fieldbackground=BG, foreground=TEXT, borderwidth=0, rowheight=36)
    style.configure('Treeview.Heading', background=SURFACE, foreground=TEXT, borderwidth=0, padding=8)
    style.map('Treeview', background=[('selected', SELECTED)], foreground=[('selected', TEXT)])
    style.configure('Vertical.TScrollbar', background=BORDER, troughcolor=BG, borderwidth=0, arrowsize=12)
    style.configure('TNotebook', background=BG, borderwidth=0)
    style.configure('TNotebook.Tab', background=SURFACE, foreground=MUTED, padding=(12, 8))
    style.map('TNotebook.Tab', background=[('selected', SELECTED)], foreground=[('selected', TEXT)])


def update_widgets(root, old_palette):
    """Recolor existing native widgets, not rebuild them or lose their contents."""
    mapping = {value: globals()[key] for key, value in old_palette.items()}
    def recolor(widget):
        options = widget.keys()
        for option in ('background', 'foreground', 'insertbackground', 'selectbackground',
                       'selectforeground', 'highlightbackground', 'highlightcolor', 'activebackground', 'activeforeground'):
            if option in options:
                current = str(widget.cget(option))
                if current in mapping:
                    widget.configure(**{option: mapping[current]})
        if 'font' in options:
            actual = tkfont.Font(root=root, font=widget.cget('font')).actual()
            widget.configure(font=(FONT, actual['size'], actual['weight'], actual['slant']))
        if isinstance(widget, tk.Text):
            for tag in widget.tag_names():
                color = widget.tag_cget(tag, 'foreground')
                if color in mapping:
                    widget.tag_configure(tag, foreground=mapping[color])
                font_value = widget.tag_cget(tag, 'font')
                if font_value:
                    actual = tkfont.Font(root=root, font=font_value).actual()
                    widget.tag_configure(tag, font=(FONT, actual['size'], actual['weight']))
        for child in widget.winfo_children():
            recolor(child)
        if hasattr(widget, 'refresh_theme'):
            widget.refresh_theme()
    recolor(root)
