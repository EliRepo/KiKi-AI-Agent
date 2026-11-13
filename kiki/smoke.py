"""Opt-in packaged-app check; no personal database, network, downloads or interaction."""
import json
from pathlib import Path
import tempfile
import tkinter as tk
from kiki.infrastructure.memory import Memory
from kiki.infrastructure.settings import Settings
from kiki.ui.desktop import App
from kiki.ui import appearance
from kiki.domain.actions import ProposalState


def run_smoke(output):
    result = {'ok': False}
    root, memory = None, None
    try:
        with tempfile.TemporaryDirectory(prefix='kiki-smoke-') as folder:
            memory = Memory(':memory:')
            root = tk.Tk()
            root.withdraw()
            app = App(root, memory, Settings(), Path(folder))
            root.update_idletasks()
            proposal = app.agent.prepare('Guarde: teste fictício do pacote')
            completed = app.agent.confirm(proposal.id)
            if completed.state is not ProposalState.EXECUTED:
                raise RuntimeError(completed.error or 'Pedido não executado')
            if memory.get_note(completed.result.note_id).text != 'teste fictício do pacote':
                raise RuntimeError('Persistência inconsistente')
            font_dir = Path(__file__).parent / 'assets' / 'fonts'
            if not all((font_dir / name).is_file() for name in ('Inter-Regular.ttf', 'Inter-Bold.ttf', 'LICENSE.txt')):
                raise RuntimeError('Fontes ou licença ausentes no pacote')
            result = {'ok': True, 'tk': root.tk.call('info', 'patchlevel'),
                      'font': appearance.FONT, 'pages': list(app.workspace.pages),
                      'settings_window': bool(app.settings_window.winfo_exists()),
                      'schema': memory.db.execute('PRAGMA user_version').fetchone()[0],
                      'confirmed_note_id': completed.result.note_id,
                      'data': 'fictional, in-memory SQLite; temporary settings; no network'}
    except Exception as error:
        result['error'] = f'{type(error).__name__}: {error}'
    finally:
        if root is not None:
            for callback in root.tk.call('after', 'info'):
                root.after_cancel(callback)
            root.destroy()
        if memory is not None:
            memory.db.close()
    Path(output).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if result['ok'] else 1
