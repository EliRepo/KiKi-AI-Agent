"""Multiline composer with the Entry interface used by the desktop controller."""
import tkinter as tk


class ChatInput(tk.Text):
    def get(self, first='1.0', last='end-1c'):
        return super().get('1.0' if first == 0 else first, last)

    def insert(self, index, text, *tags):
        return super().insert('1.0' if index == 0 else index, text, *tags)

    def delete(self, first, last=None):
        return super().delete('1.0' if first == 0 else first, last)

    def newline(self, event=None):
        self.insert('insert', '\n')
        return 'break'
