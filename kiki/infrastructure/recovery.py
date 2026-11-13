"""Recover a supported SQLite backup into a new file, never over the current database."""
from contextlib import closing
from pathlib import Path
import sqlite3

from kiki.infrastructure.migrations import SCHEMA_VERSION, _validate_schema


def restore_backup_copy(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination:
        raise ValueError('Escolha um arquivo novo; a cópia original deve ser preservada.')
    if destination.exists():
        raise FileExistsError('O destino já existe. Escolha um nome novo; nenhum arquivo será substituído.')
    # mode=ro refuses a missing source instead of silently creating an empty database.
    with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True)) as original:
        original.execute('BEGIN')
        if original.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
            raise ValueError('A cópia não passou na verificação de integridade. Preserve o arquivo original.')
        version = original.execute('PRAGMA user_version').fetchone()[0]
        if version > SCHEMA_VERSION:
            raise ValueError('A cópia pertence a uma versão mais nova da KiKi. Atualize o aplicativo.')
        _validate_schema(original, version)
        # Exclusive creation prevents overwriting even if the target appears after the initial check.
        with destination.open('xb'):
            pass
        try:
            with closing(sqlite3.connect(destination)) as restored:
                original.backup(restored)
                if restored.execute('PRAGMA integrity_check').fetchall() != [('ok',)]:
                    raise ValueError('Não foi possível verificar o arquivo restaurado.')
        except Exception:
            destination.unlink(missing_ok=True)
            raise
    return destination
