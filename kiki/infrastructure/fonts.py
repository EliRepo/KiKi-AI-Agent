"""Private font registration: no administrator privileges or registry changes."""
import os
from pathlib import Path

_loaded = False


def load_bundled_fonts():
    global _loaded
    if _loaded or os.name != 'nt':
        return
    import ctypes
    folder = Path(__file__).resolve().parent.parent / 'assets' / 'fonts'
    for path in folder.glob('Inter-*.ttf'):
        ctypes.windll.gdi32.AddFontResourceExW(str(path), 0x10, 0)
    _loaded = True
